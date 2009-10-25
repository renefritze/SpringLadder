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
	def __init__(self,alchemy_uri, verbose=False):
		print "loading db at " + alchemy_uri
		self.engine = create_engine(alchemy_uri, echo=verbose)
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
			self.AddOption( ladderid, True, "battletype", "0" )#default for all ladders
		else:
			raise ElementExistsException( ladder )
		return ladderid

	def RemoveLadder(self, ladder_id ):
		session = self.sessionmaker()

		ladder = session.query( Ladder ).filter( Ladder.id == ladder_id ).first()

		if ladder:
			session.delete( ladder )
			session.commit()
			session.close()
		else:
			raise ElementNotFoundException( Ladder(id) )
	
	def GetLadderName(self, ladder_id):
		session = self.sessionmaker()

		ladder = session.query( Ladder ).filter( Ladder.id == ladder_id ).first()
		laddername = ""
		if ladder:
			laddername = ladder.name
		session.close()
		return laddername
			
	def LadderExists(self, id ):
		session = self.sessionmaker()
		count = session.query( Ladder ).filter( Ladder.id == id ).count()
		session.close()
		return count == 1
			
	def AddOption(self, ladderID, is_whitelist, optionkey, optionvalue  ):
		session = self.sessionmaker()

		if not self.LadderExists( ladderID ):
			raise ElementNotFoundException( Ladder( ladderID ) )
	
		option = session.query( Option ).filter( Option.ladder_id == ladderID ).filter( Option.key == optionkey ).filter( Option.value == optionvalue ).first()
		#should this reset an key.val pair if already exists?
		if option:
			raise ElementExistsException( option )
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
		
	def GetOptionKeyExists(self, ladder_id, whitelist_only, keyname ):
		session = self.sessionmaker()
		count = session.query( Option ).filter( Option.ladder_id == ladder_id ).filter( Option.is_whitelist == whitelist_only).filter( Option.key == keyname ).count()
		session.close()
		return count > 0
	
	def GetOptionKeyValueExists(self, ladder_id, whitelist_only, keyname, value ):
		session = self.sessionmaker()
		count = session.query( Option ).filter( Option.ladder_id == ladder_id ).filter( Option.is_whitelist == whitelist_only).filter( Option.key == keyname ).filter( Option.value == value ).count()
		session.close()
		return count == 1
		
	def DeleteOption( self, ladder_id, whitelist_only, keyname, value ):
		session = self.sessionmaker()
		option = session.query( Option ).filter( Option.ladder_id == ladder_id ).filter( Option.is_whitelist == whitelist_only).filter( Option.key == keyname ).filter( Option.value == value ).first()
		if option:
			session.delete( option )
			session.commit()
		#else
			#raise ElementNotFoundException( Option( 
		session.close()

	def GetLadder(self, ladder_id ):
		session = self.sessionmaker()
		ladder = session.query(Ladder).filter( Ladder.id == ladder_id ).first()
		session.close()
		if not ladder:
			raise ElementNotFoundException( Ladder( ladderID ) )
		else:
			return ladder

	def GetLadderOption(self, ladder_id, field ):
		session = self.sessionmaker()
		ladder = session.query(Ladder).filter( Ladder.id == ladder_id ).first()
		session.close()
		if not ladder:
			raise ElementNotFoundException( Ladder( ladderID ) )
		else:
			return getattr(ladder, field)

	def SetLadder(self, ladder ):
		session = self.sessionmaker()
		existing_ladder = session.query(Ladder).filter( Ladder.id == ladder.id ).first()
		if not existing_ladder:
			session.close()
			raise ElementNotFoundException( ladder )
		else:
			#existing_ladder = ladder
			existing_ladder.min_team_size 	= ladder.min_team_size
			existing_ladder.max_team_size 	= ladder.max_team_size
			existing_ladder.min_ally_size 	= ladder.min_ally_size
			existing_ladder.max_ally_size 	= ladder.max_ally_size
			existing_ladder.min_ally_count 	= ladder.min_ally_count
			existing_ladder.max_ally_count 	= ladder.max_ally_count
			existing_ladder.min_team_count 	= ladder.min_team_count
			existing_ladder.max_team_count 	= ladder.max_team_count
			session.commit()
			session.close()

	def CopyLadder( self, source_id, target_name ):
		session = self.sessionmaker()
		source_ladder = session.query(Ladder).filter( Ladder.id == source_id ).first()
		if not source_ladder:
			raise ElementNotFoundException( Ladder( source_id ) )
		else:
			target_ladder = Ladder( target_name )
			target_ladder.min_team_size 	= source_ladder.min_team_size
			target_ladder.max_team_size 	= source_ladder.max_team_size 	
			target_ladder.min_ally_size 	= source_ladder.min_ally_size
			target_ladder.max_ally_size 	= source_ladder.max_ally_size
			target_ladder.min_ally_count 	= source_ladder.min_ally_count
			target_ladder.max_ally_count 	= source_ladder.max_ally_count
			target_ladder.min_team_count 	= source_ladder.min_team_count
			target_ladder.max_team_count 	= source_ladder.max_team_count
			session.add( target_ladder )
			session.commit()
			source_options = session.query( Option ).filter( Option.ladder_id == source_id )
			for opt in source_options:
				new_opt = Option( opt.key, opt.value, opt.is_whitelist )
				new_opt.ladder_id = target_ladder.id
				session.add( new_opt )
				session.commit()
		session.close()

		

