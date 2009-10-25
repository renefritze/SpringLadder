# -*- coding: utf-8 -*-
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *
from datetime import datetime

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

