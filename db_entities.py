# -*- coding: utf-8 -*-
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *
from datetime import datetime

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

Base = declarative_base()

class Ladder(Base):
	__tablename__ = 'ladders'
	id = Column( Integer, primary_key=True )
	name = Column( String(100) )
	#description = Column( whatever type means variable lengh text ( TEXT ?? ) )
	min_team_size 	= Column( Integer )
	max_team_size 	= Column( Integer )
	min_ally_size 	= Column( Integer )
	max_ally_size 	= Column( Integer )
	min_ally_count = Column( Integer )
	max_ally_count = Column( Integer )
	min_team_count = Column( Integer )
	max_team_count = Column( Integer )


	def __init__(self, name):
		self.name = name
		#!TODO sane default vals
		self.min_team_size 	= 1
		self.max_team_size 	= 1
		self.min_ally_size 	= 1
		self.max_ally_size 	= 1
		self.min_ally_count = 1
		self.max_ally_count = 1
		self.min_team_count = 1
		self.max_team_count = 1

	def __str__(self):
		return "Ladder(id:%d) %s"%(self.id,self.name)


class Option(Base):
	__tablename__ = 'options'
	id = Column( Integer, primary_key=True )
	ladder_id = Column( Integer, ForeignKey( 'ladders.id') )
	key = Column( String(100) )
	value = Column( String(100) )
	is_whitelist = Column( Boolean )

	def __init__(self,key,value,is_whitelist):
		self.key = key
		self.value = value
		self.is_whitelist = is_whitelist

	def __str__(self):
		return "Option(id:%d) %s -> %s (%s)"%(self.id,self.key, self.value, "wl" if self.is_whitelist else "bl")

class Match(Base):
	__tablename__ = 'matches'
	id = Column( Integer, primary_key=True )

    #def __init__(self,name):
        #self.name = name


class Player(Base):
	__tablename__ = 'players'
	id = Column( Integer, primary_key=True )
	nick = Column( String(50) )

	def __init__(self, nick):
		self.nick = nick

	def __str__(self):
		return "Player(id:%d) %s "%(self.id, self.nick)