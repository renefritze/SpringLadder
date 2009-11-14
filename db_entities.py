# -*- coding: utf-8 -*-
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *
from datetime import datetime

Base = declarative_base()

class Roles:
	"""need to be strongly ordered integers"""
	Banned 		= 0
	Unknown		= 1
	User		= 2
	Verified	= 3
	LadderAdmin	= 4 #special role mapped in ladderoptions, not Player class
	GlobalAdmin	= 5
	Owner		= 42

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

	def __init__(self, name="noname"):
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

	adminkey		= 'ladderadmin'

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
	role			= Column( Integer )
	do_hide_results = Column( Boolean )

	def __init__(self, nick='noname', role=Roles.User, pw=''):
		self.nick 		= nick
		self.role 		= role
		do_hide_results = False

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
	results			= relation("Result", 		order_by="Result.died" )


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
	disconnect		= Column( Integer )
	quit			= Column( Integer )
	died			= Column( Integer )
	desync			= Column( Integer )
	timeout			= Column( Integer )
	connected		= Column( Boolean )

	player			= relation(Player)
	match			= relation(Match)
	
	def __init__(self):
		self.team 		= -1
		self.disconnect = -1
		self.ally		= -1
		self.died		= -1
		self.desync		= -1
		self.timeout	= -1
		self.connected	= False
		self.quit		= -1


class SimpleRanks(Base):
	__tablename__	= 'simpleranks'
	id 				= Column( Integer, primary_key=True )
	player_id 		= Column( Integer, ForeignKey( Player.id ) )
	ladder_id 		= Column( Integer, ForeignKey( Ladder.id ) )
	points			= Column( Integer )

	def __init__(self):
		self.points = 0

	player			= relation("Player")

class GlickoRanks(Base):
	__tablename__	= 'glickoranks'
	id 				= Column( Integer, primary_key=True )
	player_id 		= Column( Integer, ForeignKey( Player.id ) )
	ladder_id 		= Column( Integer, ForeignKey( Ladder.id ) )
	rating			= Column( Float )
	rd				= Column( Float )

	def __init__(self):
		self.rating = 1500
		self.rd		=  350

	player			= relation("Player")
