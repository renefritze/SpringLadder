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
			
	def GetLadderList(self):
		session = self.sessionmaker()

		ladders = session.query(Ladder).order_by(Ladder.name)

		return ladders

helpstring_admin = """
!ladderchangemod ladderID modname : sets the mod for given ladder ID
!ladderchangecontrolteamsize ladderID value : sets the control team size (player ID) used by the ladder
!ladderchangecontrolteamsize ladderID min max : sets the control team size (player ID) used by the ladder
!ladderchangeallysize ladderID value : sets the ally team size used by the ladder
!ladderchangeallysize ladderID min max : sets the ally team size used by the ladder
!ladderaddoption ladderID blacklist/whitelist optionkey optionvalue : adds a new rule to the ladder, blacklist/whitelist is boolean and 1 means whitelist, a given key cannot have a whitelist and blacklist at the same time
!ladderremoveoption ladderID optionkey optionvalue : removes optionvalue from the ladder rules, if the optionkey has no values anymore it will be automatically removed
!ladderaddmap ladderID blacklist/whitelist mapname : adds a new map rule to the ladder, blacklist/whitelist is boolean and 1 means whitelist, a ladder cannot have a map whitelist and blacklist at the same time
!ladderremovemap ladderID mapname : removes mapname from the ladder map rules"""


helpstring_user = """
!ladderlistoptions ladderID : lists enforced options for given ladderID
!ladderlistmaps ladderID : lists enforced maps for given ladderID
!score ladderID : lists scores for all the players for the given ladderID
!score playername : lists scores for the given player in all ladders
!score ladderID playername : lists score for the given player for the given ladderID"""	
