# -*- coding: utf-8 -*-
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *
from datetime import datetime

class LadderOptions:
	 def __init__(self):
	 	self.modname = ""
	 	self.controlteamminsize = 1
	 	self.controlteammaxsize = 1
	 	self.allymaxsize = 1
	 	self.allyminsize = 1
	 	self.allowedoptions = dict() # option path -> list of allowed values
	 	self.restrictedoptions = dict() # option path -> list of denied value
	 	self.allowedmaps = [] # list of allowed map names
	 	self.restrictedmaps = [] # list of denied map names
	 	
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

	def __init__(self, name):
		self.name = name

	def __str__(self):
		return "Ladder %s"%(self.name)


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
		return "Option %s -> %s (%s)"%(self.key, self.value, "wl" if self.is_whitelist else "bl")

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

