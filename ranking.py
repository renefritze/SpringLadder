# -*- coding: utf-8 -*-

from db_entities import *
from sqlalchemy.exceptions import UnboundExecutionError

class RankingTable:
	header 	= []
	rows	= []

class EmptyRankingListException( Exception ):
	def __str__(self):
		return "no ranks, doh"

class IRanking():

	def Update(self,ladder_id,match,db):
		raise NotImplemented

	def GetPrintableRepresentation(self,rank_list,db):
		raise NotImplemented

	def GetWebRepresentation(self,rank_list,db):
		raise NotImplemented

	def GetDbEntityType(self):
		raise NotImplemented

	def GetCandidateOpponents(self,player_id,ladder_id):
		raise NotImplemented

	def OrderByKey(self):
		raise NotImplemented

class RankingAlgoSelector:
	algos = dict()
	available_ranking_algos = []

	def RegisterAlgo( self, instance ):
		RankingAlgoSelector.available_ranking_algos.append( instance.__class__.__name__ )
		RankingAlgoSelector.algos[RankingAlgoSelector.available_ranking_algos[-1]] =  instance

	def GetInstance(self, name ):
		if not name in RankingAlgoSelector.available_ranking_algos:
			raise ElementNotFoundException( name )
		return self.algos[name]

	def GetPrintableRepresentation(self, rank_list,db ):
		if len(rank_list) < 1:
			return 'no ranks to represent'
		else:
			el = rank_list[0]
			for algo in self.algos.values():
				if isinstance( el, algo.GetDbEntityType() ):
					return algo.GetPrintableRepresentation( rank_list,db )
			print 'no suitable algo for printing rank list found '
			return ''

	def GetCandidateOpponents(self,player_nick,ladder_id,db):
			ladder_ranking_algo = db.GetLadder( ladder_id ).ranking_algo_id
			algo_instance = GlobalRankingAlgoSelector.GetInstance( ladder_ranking_algo )
			return algo_instance.GetCandidateOpponents( player_nick,ladder_id, db )

	def GetPrintableRepresentationPlayer(self, rank_dict,db ):
		if len(rank_dict) < 1:
			raise EmptyRankingListException()
		else:
			res = ''
			for rank,rtuple in rank_dict.iteritems():
				algo_instance = self.algos[rtuple[0]]
				res += 'Ladder %s, ranking: %s'%(rtuple[1],algo_instance.GetPrintableRepresentation( [rank], db ) )
			return res

	def GetWebRepresentation(self,rank_list,db):
		if len(rank_list) < 1:
			raise EmptyRankingListException()
		el = rank_list[0]
		for algo in self.algos.values():
			if isinstance( el, algo.GetDbEntityType() ):
				return algo.GetWebRepresentation( rank_list,db )
		return None

	def ListRegisteredAlgos(self):
		res = ''
		for a in RankingAlgoSelector.available_ranking_algos:
			res += a + '\n'
		return res

def calculateWinnerOrder(match,db):
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
		session.close()
		#calculate order of deaths
		deaths = dict()
		scores = dict()

		playercount = len(result_dict)
		for name,player in result_dict.iteritems():
			if player.died > -1 and player.died < match.last_frame:
				deaths[name] = player.died
			if player.disconnect > -1 and player.disconnect < match.last_frame:
				if player.quit:
					scores[name] = -5
				elif player.timeout:
					scores[name] = -1
				elif player.kicked:
					scores[name] = 0
			if player.desync > -1 and player.desync < match.last_frame:
				scores[name] = 0
		#find last team standing
		for name in result_dict.keys():
			if name not in deaths.keys() and name not in scores.keys():
				scores[name] = playercount + 4
			elif name not in scores.keys():
				reldeath = deaths[name] / float(match.last_frame)
				scores[name] = reldeath * playercount
		return scores,result_dict

class SimpleRankAlgo(IRanking):

	def Update(self,ladder_id,match,db):

		scores, result_dict = calculateWinnerOrder(match,db)
		session = db.sessionmaker()

		for name,player in result_dict.iteritems():
			player_id = session.query( Player ).filter( Player.nick == name ).first().id
			rank = session.query( SimpleRanks ).filter( SimpleRanks.ladder_id == ladder_id ).filter( SimpleRanks.player_id == player_id ).first()
			if not rank:
				rank = SimpleRanks()
				rank.ladder_id = ladder_id
				rank.player_id = player_id
			rank.points += scores[name]
			session.add(rank)
			#must i commit everytime?
			session.commit()
		session.close()

	@staticmethod
	def GetPrintableRepresentation(rank_list,db):
		ret = ''
		s = db.sessionmaker()
		for rank in rank_list:
			s.add( rank )
			ret += 'player: %s\tscore: %4f\n'%(rank.player.nick,rank.points)
		s.close()
		return ret

	def GetWebRepresentation(self,rank_list,db):
		ret = RankingTable()
		ret.header = ['nick','score']
		s = db.sessionmaker()
		for rank in rank_list:
			s.add( rank )
			ret.rows.append( [rank.player.nick , round(rank.points,3) ] )
		s.close()
		return ret


	def GetDbEntityType(self):
		return SimpleRanks

	def OrderByKey(self):
		return SimpleRanks.points.desc()

from glicko import GlickoRankAlgo
GlobalRankingAlgoSelector = RankingAlgoSelector()
GlobalRankingAlgoSelector.RegisterAlgo( SimpleRankAlgo() )
GlobalRankingAlgoSelector.RegisterAlgo( GlickoRankAlgo() )
