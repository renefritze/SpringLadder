# -*- coding: utf-8 -*-
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *
from datetime import datetime
from db_entities import *

class ElementExistsException( Exception ):
	def __init__(self, element):
		self.element = element

	def __str__(self):
		return "Element %s already exists in db"%(self.element)

class ElementNotFoundException( Exception ):
	def __init__(self, element):
		self.element = element

	def __str__(self):
		return "Element %s not found in db"%(self.element)

class LadderDB:
	def __init__(self,alchemy_uri):
		print "loading db at " + alchemy_uri
		self.engine = create_engine(alchemy_uri, echo=True)
		self.metadata = Base.metadata
		self.metadata.bind = self.engine
		self.metadata.create_all(self.engine)
		self.sessionmaker = sessionmaker( bind=self.engine )

	def AddLadder(self, name ):
		session = self.sessionmaker()
		ladder = session.query( Ladder ).filter( Ladder.name == name ).first()
		ladderid = -1
		if not ladder: #no existing ladder with same name
			ladder = Ladder( name )
			session.add( ladder )
			session.commit()
			ladderid = ladder.id
			session.close()
		else:
			raise ElementExistsException( ladder )
		return ladderid

	def RemoveLadder(self, id ):
		session = self.sessionmaker()

		ladder = session.query( Ladder ).filter( Ladder.id == id ).first()

		if ladder:
			session.delete( ladder )
			session.commit()
			session.close()
		else:
			raise ElementNotFoundException( Ladder(id) )
			
	def LadderExists(self, id ):
		session = self.sessionmaker()

		ladder = session.query( Ladder ).filter( Ladder.id == id ).first()
		
		session.close()
		return ladder
			
	def AddOption(self, ladderID, is_whitelist, optionkey, optionvalue  ):
		session = self.sessionmaker()

		option = session.query( Option ).filter( Option.ladder_id == ladderID ).filter( Option.key == optionkey ).first()
		#should this reset an key.val pair if already exists?
		if option:
			option.value = optionvalue
			option.is_whitelist = is_whitelist
			session.commit()
		else:
			option = Option( optionkey, optionvalue, is_whitelist )
			option.ladder_id = ladderID
			session.add( option )
			session.commit()
		session.close()
			
	def GetLadderList(self,order):
		'''second parameter determines order of returned list (Ladder.name/Ladder.id for example) '''
		session = self.sessionmaker()
		ladders = session.query(Ladder).order_by(order)
		session.close()
		return ladders

	def GetOptions(self, ladder_id ):
		session = self.sessionmaker()
		options = session.query( Option ).filter( Option.ladder_id == ladder_id ).order_by( Option.key )
		session.close()
		return options

	def GetFilteredOptions(self, ladder_id, whitelist_only ):
		session = self.sessionmaker()
		options = session.query( Option ).filter( Option.ladder_id == ladder_id ).filter( Option.is_whitelist == whitelist_only).order_by( Option.key )
		session.close()
		return options
		
	def GetOptionExists(self, ladder_id, whitelist_only, keyname ):
		session = self.sessionmaker()
		values = session.query( Option ).filter( Option.ladder_id == ladder_id ).filter( Option.is_whitelist == whitelist_only).filter( Option.key == keyname ).first()
		session.close()
		return values	
	
	def GetOptionValues(self, ladder_id, whitelist_only, keyname ):
		session = self.sessionmaker()
		values = session.query( Option ).filter( Option.ladder_id == ladder_id ).filter( Option.is_whitelist == whitelist_only).filter( Option.key == keyname ).order_by( Option.value )
		session.close()
		return values
		

