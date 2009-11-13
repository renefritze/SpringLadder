# -*- coding: utf-8 -*-

from db_entities import *

class RankingTable:
	header 	= []
	rows	= []

class EmptyRankingListException( Exception ):
	def __str__(self):
		return "no ranks, doh"

class IRanking():
	
	def Update(self,ladder_id,matchresult,db):
		raise NotImplemented

	def GetPrintableRepresentation(self,rank_list,db):
		raise NotImplemented

	def GetWebRepresentation(self,rank_list,db):
		raise NotImplemented
		
	def GetDbEntityType(self):
		raise NotImplemented

	def OrderByKey(self):
		raise NotImplemented

class RankingAlgoSelector:
	algos = dict()
	available_ranking_algos = []	
		
	def RegisterAlgo( self, instance ):
		RankingAlgoSelector.available_ranking_algos.append( type(instance).__name__ )
		RankingAlgoSelector.algos[RankingAlgoSelector.available_ranking_algos[-1]] =  instance
		
	def GetInstance(self, name ):
		if not name in RankingAlgoSelector.available_ranking_algos:
			raise ElementNotFoundException( name )
		return self.algos[name]

	def GetPrintableRepresentation(self, rank_list,db ):
		if len(rank_list) < 1:
			print 'no ranks to represent'
			return 'no ranks to represent'
		else:
			el = rank_list[0]
			for algo in self.algos.values():
				if isinstance( el, algo.GetDbEntityType() ):
					return algo.GetPrintableRepresentation( rank_list,db )
			print 'no suitable algo for printing rank list found '
			return ''

	def GetPrintableRepresentationPlayer(self, rank_dict,db ):
		if len(rank_dict) < 1:
			print 'no ranks to represent'
			raise EmptyRankingListException()
		else:
			res = ''
			for rank,rtuple in rank_dict.iteritems():
				algo_instance = self.algos[rtuple[0]]
				res += 'Ladder %s, ranking: %s'%(rtuple[1],algo_instance.GetPrintableRepresentation( [rank], db ) )
			return res

	def GetWebRepresentation(self,rank_list,db):
		if len(rank_list) < 1:
			print 'no ranks to represent'
			raise EmptyRankingListException()
		el = rank_list[0]
		for algo in self.algos.values():
			if isinstance( el, algo.GetDbEntityType() ):
				return algo.GetWebRepresentation( rank_list,db )
		return None

class SimpleRankAlgo(IRanking):

	def Update(self,ladder_id,matchresult,db):
		#calculate order of deaths
		deaths = dict()
		scores = dict()
		session = db.sessionmaker()
		playercount = len(matchresult.players)
		for r in matchresult.players.values():
			session.add( r )
			
		for name,player in matchresult.players.iteritems():
			if player.died > 0:
				deaths[name] = player.died
			if player.timeout > -1:
				scores[name] = -1
			if player.disconnect > -1:
				scores[name] = -2
			if player.quit > -1:
				scores[name] = -5
			if player.desync > -1:
				scores[name] = 0
		
		endframe = matchresult.game_over
		#find last team standing
		for name in matchresult.players.keys():
			if name not in deaths.keys() and name not in scores.keys():
				scores[name] = playercount + 4
			elif name not in scores.keys():
				reldeath = deaths[name] / float(endframe)
				scores[name] = reldeath * playercount
		print 'scores ',scores
		for name,player in matchresult.players.iteritems():
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

GlobalRankingAlgoSelector = RankingAlgoSelector()
GlobalRankingAlgoSelector.RegisterAlgo( SimpleRankAlgo() )
