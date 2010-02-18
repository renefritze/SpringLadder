# -*- coding: utf-8 -*-
from ranking import IRanking,RankingTable
from db_entities import GlickoRanks,Player,Match,Result
import math,time,datetime
from sqlalchemy.exceptions import UnboundExecutionError
class GlickoRankAlgo(IRanking):

	q = math.log( 10.0 ) / 400.0

	def __init__(self):
		self.c = 64.0
		self.rd_lower_bound = 50.0

	def Update(self,ladder_id,match,db):
		session = db.sessionmaker()
		#session.add( match ) #w/o this match is unbound, no lazy load of results
		result_dict = dict()
		try:
			for r in match.results:
				result_dict[r.player.nick] = r
		except UnboundExecutionError,u:
			session.add( match )
			for r in match.results:
				session.add( r )
				result_dict[r.player.nick] = r
		#calculate order of deaths
		deaths = dict()
		scores = dict()

		playercount = len(result_dict)
		for name,player in result_dict.iteritems():
			if player.died > 0:
				deaths[name] = player.died
			if player.timeout:
				scores[name] = -1
			if player.disconnect > -1:
				scores[name] = -2
			if player.quit:
				scores[name] = -5
			if player.desync > -1:
				scores[name] = 0

		#find last team standing
		for name in result_dict.keys():
			if name not in deaths.keys() and name not in scores.keys():
				scores[name] = playercount + 4
			elif name not in scores.keys():
				reldeath = deaths[name] / float(match.last_frame)
				scores[name] = reldeath * playercount

		#step one
		pre = dict() #name -> GlickoRanks
		match_query = session.query( Match ).filter( Match.ladder_id == ladder_id ).filter( Match.date <= match.date ).order_by( Match.date.desc() )
		num_matches = match_query.count()
		if num_matches > 0:
			prior_match = match_query.first()
			first_match = match_query[num_matches-1]
			first_match_unixT = time.mktime(first_match.date.timetuple())
		else:
			first_match_unixT = time.mktime(datetime.now().timetuple())
		last_match_unixT = first_match_unixT
		avg_match_delta = db.GetAvgMatchDelta( ladder_id, match.date )
		for name,result in result_dict.iteritems():
			#get number of matches since last for player
			#if match_query.count() < 2:
			p_result_query = session.query( Result ).filter( Result.player_id == result.player_id ).filter( Result.ladder_id == ladder_id ).filter(Result.date <= match.date).order_by( Result.id.desc() )
			if p_result_query.count() > 1:
				prev_result = p_result_query[1]
				for m in match_query[1:] :
					if prev_result.match_id == m.id:
						last_match_unixT = time.mktime(m.date.timetuple())
						break
			t = ( last_match_unixT - first_match_unixT ) / avg_match_delta

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
		ret = '#position playername (Rating/Rating Deviation):\n'
		s = db.sessionmaker()
		count = 1
		for rank in rank_list:
			s.add( rank )
			ret += '#%d %s\t(%2f/%4f)\n'%(count,rank.player.nick,rank.rating, rank.rd)
			count = count +1
		s.close()
		return ret

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
