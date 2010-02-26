# -*- coding: utf-8 -*-
from ranking import IRanking,RankingTable,calculateWinnerOrder
from db_entities import GlickoRanks,Player,Match,Result
from sqlalchemy import or_, and_
import math,time,datetime
class GlickoRankAlgo(IRanking):

	q = math.log( 10.0 ) / 400.0

	def __init__(self):
		self.c = 32.0
		self.rd_lower_bound = 50.0

	def Update(self,ladder_id,match,db):
		scores, result_dict = calculateWinnerOrder(match,db)

		session = db.sessionmaker()
		#step one
		pre = dict() #name -> GlickoRanks
		avg_match_delta = db.GetAvgMatchDelta( ladder_id )
		for name,result in result_dict.iteritems():
			previous_match = session.query( Result ).filter( Result.player_id == result.player_id ).filter( Result.ladder_id == ladder_id ).filter(Result.date < match.date).order_by( Result.date.desc() ).filter( Result.id != match.id ).first()
			if previous_match:
				last_match_unixT = time.mktime(match.date.timetuple())
				prev_match_unixT = time.mktime(previous_match.date.timetuple())
			else:
				prev_match_unixT = last_match_unixT = 0
			delta = last_match_unixT - prev_match_unixT
			t = delta / avg_match_delta
			db.UpdateAvgMatchDelta( ladder_id, delta )

			player_id = session.query( Player ).filter( Player.nick == name ).first().id
			rank = session.query( GlickoRanks ).filter( GlickoRanks.ladder_id == ladder_id ).filter( GlickoRanks.player_id == player_id ).first()
			if not rank:
				rank = GlickoRanks()
				rank.ladder_id = ladder_id
				rank.player_id = player_id
			#actual calc
			else:
				rank.rd = min( math.sqrt( rank.rd*rank.rd + self.c*self.c * t ), 350.0 )#increase rd up to 350
			session.add(rank)
			#must i commit everytime?
			session.commit()
			pre[name] = rank
		#end step 1

		#step 2
		post = dict() #name -> ( r\' , RD\' )
		# build rd_j and r_j and s_j lists for each player
		lists = dict() # name -> ( [r_j] , [rd_j] , [s_j] )
		for name,result in result_dict.iteritems():
			r_j_list = []
			rd_j_list = []
			s_j_list = []
			my_score = scores[name]
			my_ally = result.ally
			for other,other_result in result_dict.iteritems():
				if name == other or other_result.ally == my_ally:
					continue
				r_j_list.append( pre[other].rating )
				rd_j_list.append( pre[other].rd )
				other_score = scores[other]
				if my_score > other_score:
					s_j_list.append( 1.0 )
				elif my_score < other_score:
					s_j_list.append( 0.0 )
				else:
					s_j_list.append( 0.5 )
			lists[name] = ( r_j_list, rd_j_list, s_j_list )

		#compute updates
		for name in result_dict.keys():
			r = pre[name].rating
			RD = pre[name].rd
			r_j_list = lists[name][0]
			rd_j_list = lists[name][1]
			s_j_list = lists[name][2]
			ds = self.d_squared( r, r_j_list, rd_j_list )
			denom = ( 1.0 / ( RD*RD ) ) + ( 1.0 / ds )
			# calc r'
			su = 0.0
			for j in range(len(r_j_list)):
				su += self.g( rd_j_list[j] ) * (s_j_list[j] - self.E( r, r_j_list[j], rd_j_list[j] ) )
			r_new = r + ( ( self.q / denom ) * su )
			rd_new = math.sqrt( 1.0 / denom )
			post[name] = ( r_new, rd_new )

		#commit updates
		for name in result_dict.keys():
			rank = pre[name]
			rank.rating = post[name][0]
			rank.rd = max(post[name][1], self.rd_lower_bound )
			session.add ( rank )
			session.commit()
		#end step 2
		session.close()

	@staticmethod
	def g( rd ):
		return ( 1.0 / math.sqrt( 1.0 + 3.0*GlickoRankAlgo.q*GlickoRankAlgo.q * rd*rd / ( math.pi*math.pi ) ) )

	@staticmethod
	def E( r, r_j, rd_j ):
		return 1.0 / ( 1.0 + math.pow( 10, -1 * GlickoRankAlgo.g( rd_j ) * ( r - r_j ) / 400.0 ) )

	@staticmethod
	def d_squared( r, r_j_list, rd_j_list ):
		s = 0.0
		assert len(r_j_list)  == len(rd_j_list)
		assert len(r_j_list) > 0
		assert GlickoRankAlgo.q > 0 or GlickoRankAlgo.q < 0
		for j in range( len(r_j_list) ):
			g_val = GlickoRankAlgo.g( rd_j_list[j] )
			g_val *= g_val
			E_val = GlickoRankAlgo.E( r, r_j_list[j], rd_j_list[j] )
			s += g_val * E_val * ( 1.0 - E_val )
		return 1.0 / ( GlickoRankAlgo.q*GlickoRankAlgo.q * s )

	@staticmethod
	def GetPrintableRepresentation(rank_list,db):
		ret = '#position playername\t\t(Rating/RatingDeviation):\n'
		s = db.sessionmaker()
		count = 0
		previousrating = -1
		same_rating_in_a_row = 0
		for rank in rank_list:
			s.add( rank )
			if rank.rating != previousrating: # give the same position to players with the same rank
				if same_rating_in_a_row == 0:
					count += 1
				else:
					count += same_rating_in_a_row +1
					same_rating_in_a_row = 0
			else:
				same_rating_in_a_row += 1
			ret += '#%d %s\t(%4.2f/%3.0f)\n'%(count,rank.player.nick,rank.rating, rank.rd)
			previousrating = rank.rating
		s.close()
		return ret

	def GetCandidateOpponents(self,player_nick,ladder_id,db):
		player = db.GetPlayer( player_nick )
		player_id = player.id
		session = db.sessionmaker()
		playerrank = session.query( GlickoRanks ).filter( GlickoRanks.player_id == player_id ).filter( GlickoRanks.ladder_id == ladder_id ).first()
		if not playerrank: # use default rank, but don't add it to the db yet
			playerrank = GlickoRanks()
		playerminvalue = playerrank.rating - playerrank.rd
		playermaxvalue = playerrank.rating + playerrank.rd
		opponent_q = session.query( GlickoRanks ).filter( GlickoRanks.player_id != player_id ) \
			.filter( GlickoRanks.ladder_id == ladder_id )
		ops1 = opponent_q \
			.filter( and_ ( ( (GlickoRanks.rating + GlickoRanks.rd) >= playerminvalue ), \
								 ( ( GlickoRanks.rating + GlickoRanks.rd ) <= playermaxvalue ) ) )
		ops2 = opponent_q \
			.filter( and_( ( playermaxvalue >=  ( GlickoRanks.rating - GlickoRanks.rd ) ), \
								( playermaxvalue <= (GlickoRanks.rating + GlickoRanks.rd) ) )  ) \
			#.order_by( math.fabs(GlickoRanks.rating - playerrank.rating ) )
		opponents = []
		opponents_ranks = dict()
		ops = ops1.all() + ops2.all()
		ops.sort( lambda x,y : cmp( math.fabs( x.rating - playerrank.rating ), math.fabs( y.rating - playerrank.rating ) ) )
		for op in ops:
			opponents.append(op.player.nick)
			opponents_ranks[op.player.nick] = '#%d %s\t(%4.2f/%3.0f)\n'%(db.GetPlayerPosition(ladder_id, op.player.id),op.player.nick,op.rating, op.rd)
		session.close()
		return opponents, opponents_ranks

	def GetWebRepresentation(self,rank_list,db):
		ret = RankingTable()
		ret.header = ['nick','rating','RD']
		ret.rows = []
		s = db.sessionmaker()
		for rank in rank_list:
			s.add( rank )
			ret.rows.append( [rank.player.nick , round(rank.rating,2), round(rank.rd,4) ] )
		s.close()
		return ret


	def GetDbEntityType(self):
		return GlickoRanks

	def OrderByKey(self):
		return GlickoRanks.rating.desc()
