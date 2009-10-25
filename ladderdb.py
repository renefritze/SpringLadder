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

		if not ladder: #no existing ladder with same name
			ladder = Ladder( name )
			session.add( ladder )
			session.commit()
			session.close()
		else:
			raise ElementExistsException( ladder )

	def RemoveLadder(self, id ):
		session = self.sessionmaker()

		ladder = session.query( Ladder ).filter( Ladder.id == id ).first()

		if ladder:
			session.delete( ladder )
			session.commit()
			session.close()
		else:
			raise ElementNotFoundException( Ladder(id) )
			
	def AddOption(self, ladderID, blacklist, optionkey, optionvalue  ):
		session = self.sessionmaker()

		option = session.query( Option ).filter( Option.key == optionkey ).first()
		#should this reset an key.val pair if already exists?
			
	def GetLadderList(self,order):
		'''second parameter determines order of returned list (Ladder.name/Ladder.id for example) '''
		session = self.sessionmaker()

		ladders = session.query(Ladder).order_by(order)
		session.close()

		return ladders

