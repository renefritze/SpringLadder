# -*- coding: utf-8 -*-


class IRanking():
	
	def Update(ladder_id,matchresult,db):
		raise NotImplemented

class RankingAlgoSelector:
	available_ranking_algos = ['simple']

	def __init__(self):
		self.algos = dict()
		[available_ranking_algos[0]] =  SimpleRanks()

	def GetInstance(self, name ):
		if not name in available_ranking_algos
			raise ElementNotFoundException( name )
		return self.algos[name]

class SimpleRanks(IRanking):

	def Update(ladder_id,matchresult,db):
		return ''


GlobalRankingAlgoSelector = RankingAlgoSelector()