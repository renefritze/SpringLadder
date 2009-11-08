# -*- coding: utf-8 -*-
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *
from datetime import datetime
"""
class LadderMatch:
	def __init__(self):
		self.timestamp = 0
		self.result = 0
		self.winnerid = -1
		self.players = dict()
		self.teams = dict()

class ControlTeam:
	def __init__(self):
		self.playeridlist = []
		self.allyteamidlist = []
		
class Player:
	 def __init__(self):
	 	self.id = -1
	 	self.controlteam = -1
	 	self.ally = -1
	 	self.spectator = False
	 	self.isbot = False
"""
Base = declarative_base()

class Ladder(Base):
	__tablename__ 	= 'ladders'
	id 				= Column( Integer, primary_key=True )
	name 			= Column( String(100) )
	description 	= Column( Text )
	min_team_size 	= Column( Integer )
	max_team_size 	= Column( Integer )
	min_ally_size 	= Column( Integer )
	max_ally_size 	= Column( Integer )
	min_ally_count 	= Column( Integer )
	max_ally_count 	= Column( Integer )
	min_team_count 	= Column( Integer )
	max_team_count 	= Column( Integer )
	ranking_algo_id	= Column( String(30) )

	def __init__(self):
		self.__init__("noname")

	def __init__(self, name):
		self.name = name
		self.min_team_size 	= 1
		self.max_team_size 	= 1
		self.min_ally_size 	= 1
		self.max_ally_size 	= 1
		self.min_ally_count = 2
		self.max_ally_count = 2
		self.min_team_count = 2
		self.max_team_count = 2

	def __str__(self):
		return "Ladder(id:%d) %s\n\tteam-size (%d/%d)\n\tally-size (%d/%d)\n\tteam-count (%d/%d)\n\tally-count (%d/%d)"%(self.id,self.name,self.min_team_size,self.max_team_size,self.min_ally_size,self.max_ally_size,self.min_team_count,self.max_team_count,self.min_ally_count,self.max_ally_count)


class Option(Base):
	__tablename__ 	= 'options'
	id 				= Column( Integer, primary_key=True )
	ladder_id 		= Column( Integer, ForeignKey( Ladder.id ) )
	key 			= Column( String(100) )
	value 			= Column( String(100) )
	is_whitelist 	= Column( Boolean )

	def __init__(self,key='defaultkey',value='emptyvalue',is_whitelist=True):
		self.key = key
		self.value = value
		self.is_whitelist = is_whitelist

	def __str__(self):
		return "Option(id:%d) %s -> %s (%s)"%(self.id,self.key, self.value, "wl" if self.is_whitelist else "bl")

class Player(Base):
	__tablename__ 	= 'players'
	id 				= Column( Integer, primary_key=True )
	nick 			= Column( String(50) )
	pwhash 			= Column( String(80) )

	def __init__(self, nick):
		self.nick = nick

	def __str__(self):
		return "Player(id:%d) %s "%(self.id, self.nick)

class Match(Base):
	__tablename__ 	= 'matches'
	id 				= Column( Integer, primary_key=True )
	ladder_id 		= Column( Integer, ForeignKey( Ladder.id ) )
	date 			= Column( DateTime )
	modname 		= Column( String( 60 ) )
	mapname 		= Column( String( 60 ) )
	replay 			= Column( String( 200 ) )
	duration 		= Column( Interval )

	settings    	= relation("MatchSetting", 	order_by="MatchSetting.key" )#, backref="match" )#this would auto-create a relation in MatchSetting too
	results			= relation("Result", 		order_by="Result.team" )
	

class MatchSetting(Base):
	__tablename__ 	= 'matchsettings'
	id 				= Column( Integer, primary_key=True )
	key 			= Column( String(40) )
	value 			= Column( String(80) )
	match_id 		= Column( Integer, ForeignKey( Match.id ) )
	
class Result(Base):
	__tablename__ 	= 'results'
	id 				= Column( Integer, primary_key=True )
	player_id 		= Column( Integer, ForeignKey( Player.id ) )
	match_id 		= Column( Integer, ForeignKey( Match.id ) )
	team			= Column( Integer )
	ally			= Column( Integer )
	place			= Column( Integer )
	disconnect		= Column( Integer )
	quit			= Column( Integer )
	died			= Column( Integer )
	desync			= Column( Integer )
	timeout			= Column( Integer )
	connected		= Column( Boolean )
	#whatever else stats trakced below
	
class SimpleRanks(Base):
	id 				= Column( Integer, primary_key=True )
	player_id 		= Column( Integer, ForeignKey( Player.id ) )
	ladder_id 		= Column( Integer, ForeignKey( Ladder.id ) )
	wins			= Column( Integer )
	losses			= Column( Integer )
	draws			= Column( Integer )
	

	
