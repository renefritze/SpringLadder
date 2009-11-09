# -*- coding: utf-8 -*-

from db_entities import *

class IRanking():
	
	def Update(self,ladder_id,matchresult,db):
		raise NotImplemented

	def GetPrintableRepresentation(self,rank_list,db):
		raise NotImplemented

	def GetDbEntityType(self):
		raise NotImplemented

class RankingAlgoSelector:
	available_ranking_algos = ['simple'] #might actually work just via type switching

	def __init__(self):
		self.algos = dict()
		self.algos[RankingAlgoSelector.available_ranking_algos[0]] =  SimpleRankAlgo()

	def GetInstance(self, name ):
		if not name in RankingAlgoSelector.available_ranking_algos:
			raise ElementNotFoundException( name )
		return self.algos[name]

	def GetPrintableRepresentation(self, rank_list,db ):
		if len(rank_list) < 1:
			print 'no ranks to represent'
			return ''
		else:
			el = rank_list[0]
			for algo in self.algos.values():
				if isinstance( el, algo.GetDbEntityType() ):
					return algo.GetPrintableRepresentation( rank_list,db )
			print 'no suitable algo for printing rank list found '
			return ''
			

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
				deaths[player.died] = name
			if player.timeout > -1:
				scores[name] = -1
			if player.disconnect > -1:
				scores[name] = -2
			if player.quit > -1:
				scores[name] = -5
			if player.desync > -1:
				scores[name] = 0
			
		#find last team standing
		for name in matchresult.players.keys():
			if name not in deaths.values() and name not in scores.keys():
				scores[name] = playercount
			else:
				scores[name] = 2134
		
		#qu = session.
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

	def GetPrintableRepresentation(self,rank_list,db):
		ret = ''
		s = db.sessionmaker()
		for rank in rank_list:
			s.add( rank )
			ret += 'player: %s\tscore: %4d\n'%(rank.player.nick,rank.points)
		return ret
			
	def GetDbEntityType(self):
		return SimpleRanks

GlobalRankingAlgoSelector = RankingAlgoSelector()

#team			= Column( Integer )
#ally			= Column( Integer )
#disconnect		= Column( Integer )
#quit			= Column( Integer )
#died			= Column( Integer )
#desync			= Column( Integer )
#timeout			= Column( Integer )
#connected		= Column( Boolean )