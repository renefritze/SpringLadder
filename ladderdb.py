# -*- coding: utf-8 -*-
#from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *
from sqlalchemy import exc
import traceback, datetime, math, hashlib
from db_entities import *
from ranking import *
from match import *
import time
from customlog import *

current_db_rev = 4

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

class DbConnectionLostException( Exception ):
	def __init__( self, trace ):
		self.trace = trace
	def __str__(self):
		return "Database connection temporarily lost during query"
	def getTrace(self):
		return self.trace

class LadderDB:
	def Connect(self):
		self.engine = create_engine(self.alchemy_uri, echo=self.verbose, pool_size=10, max_overflow=20)
		self.metadata = Base.metadata
		self.metadata.bind = self.engine
		self.metadata.create_all(self.engine)
		self.sessionmaker = sessionmaker( bind=self.engine )

	def __init__(self,alchemy_uri,owner=[], verbose=False):
		global current_db_rev
#		print "loading db at " + alchemy_uri
		self.alchemy_uri = alchemy_uri
		self.verbose = verbose
		self.Connect()
		oldrev = self.GetDBRevision()
		self.UpdateDBScheme( oldrev, current_db_rev )
		self.SetDBRevision( current_db_rev )
		self.SetOwner(owner)

	def getSession(self):
		return self.sessionmaker()

	def AddLadder(self, name, ranking_algo_id = 0 ):
		session = self.sessionmaker()
		ladder = session.query( Ladder ).filter( Ladder.name == name ).first()
		ladderid = -1
		if not ladder: #no existing ladder with same name
			ladder = Ladder( name )
			ladder.ranking_algo_id = GlobalRankingAlgoSelector.available_ranking_algos[-1]
			session.add( ladder )
			session.commit()
			ladderid = ladder.id

			session.close()
			self.AddOption( ladderid, True, "battletype", "0" )#default for all ladders
		else:
			session.close()
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
			session.close()
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
			session.close()
			raise ElementNotFoundException( Ladder( ladderID ) )

		option = session.query( Option ).filter( Option.ladder_id == ladderID ).filter( Option.key == optionkey ).filter( Option.value == optionvalue ).first()
		#should this reset an key.val pair if already exists?
		if option:
			session.close()
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
			raise ElementNotFoundException( Ladder( ladder_id ) )
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
			session.close()
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

	def AddPlayer(self,name,role,pw=''):
		session = self.sessionmaker()
		player = session.query( Player ).filter( Player.nick == name ).first()
		if not player:
			player = Player( name,role, pw )
			session.add( player )
			session.commit()
		session.close()

	def AssignServerID(self,name, serverplayerid ):
		session = self.sessionmaker()
		player = session.query( Player ).filter( Player.nick == name ).first()
		if player:
			player.server_id = serverplayerid
			session.add( player )
			session.commit()
			session.close()
		else:
			session.close()
			raise ElementNotFoundException( str(serverplayerid) )

	def RenamePlayer(self,serverplayerid,newname):
		session = self.sessionmaker()
		player = session.query( Player ).filter( Player.server_id == serverplayerid ).first()
		if player:
			player.nick = newname
			session.add(player)
			session.commit()
			session.close()
		else:
			session.close()
			raise ElementNotFoundException( str(serverplayerid) )

	def GetPlayer( self, name ):
		session = self.sessionmaker()
		player = session.query( Player ).filter( Player.nick == name ).first()
		if not player:
			self.AddPlayer( name, Roles.User )
			player = session.query( Player ).filter( Player.nick == name ).first()
		session.close()
		return player

	def SetOwner(self,owner):
		for name in owner:
			try:
				self.AddPlayer( name,Roles.Owner, '')
			except:
				print 'error adding owner ',name

	def ReportMatch( self, matchresult, doValidation=True ):
		"""false skips validation check of output against ladder rules"""
		if not isinstance( matchresult, MatchToDbWrapper ):
			raise TypeError
		return matchresult.CommitMatch(self,doValidation)

	def GetMatchReplay( self, match_id ):
		session = self.sessionmaker()
		match = session.query( Match ).filter( Match.id == match_id ).first()
		if match:
			replaypath = match.replay
			session.close()
			return replaypath
		else:
			session.close()
			raise ElementNotFoundException( str(match_id) )

	def GetRanks( self, ladder_id, player_name=None,limit=-1 ):
		session = self.sessionmaker()
		ladder_ranking_algo = session.query( Ladder.ranking_algo_id ).filter( Ladder.id == ladder_id ).first()[0]
		algo_instance = GlobalRankingAlgoSelector.GetInstance( ladder_ranking_algo )
		entityType = algo_instance.GetDbEntityType()
		if player_name:
			player = session.query( Player ).filter( Player.nick == player_name ).first()
			if player:
				#needs to be a list so the printing in GlobalRankingAlgoSelector works
				ranks = [ session.query( entityType ).filter( entityType.ladder_id == ladder_id ).filter(entityType.player_id == player.id).first() ]
			else:
				session.close()
				raise ElementNotFoundException( Player( player_name ) )
		else:
			if limit > -1:
				ranks = session.query( entityType ).filter( entityType.ladder_id == ladder_id ).order_by( algo_instance.OrderByKey() )[0:limit]
			else:
				ranks = session.query( entityType ).filter( entityType.ladder_id == ladder_id ).order_by( algo_instance.OrderByKey() ).all()
		session.close()
		return ranks

	def GetPlayerRanks( self, player_name ):
		res = dict() # rank -> ( algoname , laddername )
		session = self.sessionmaker()
		ladders = session.query( Ladder ).all()
		player = session.query( Player ).filter( Player.nick == player_name ).first()
		if player:
			for ladder in ladders:
				aloginstance = GlobalRankingAlgoSelector.GetInstance( ladder.ranking_algo_id )
				algoname = aloginstance.__class__.__name__
				entityType = aloginstance.GetDbEntityType()
				rank = session.query( entityType ).filter( entityType.ladder_id == ladder.id ).filter(entityType.player_id == player.id).first()
				if rank:
					res[rank] = ( algoname, ladder.name )
		session.close()
		return res

	def GetPlayerPosition(self, ladder_id, player_id):
		session = self.sessionmaker()
		player = session.query( Player ).filter( Player.id == player_id ).first()
		pos = -1
		ranks = self.GetRanks( ladder_id )
		count = 0
		previousrank = None
		same_rating_in_a_row = 0
		for r in ranks:
			if r.compare( previousrank ) != 0: # give the same position to players with the same rank
				if same_rating_in_a_row == 0:
					count += 1
				else:
					count += same_rating_in_a_row +1
					same_rating_in_a_row = 0
			else:
				same_rating_in_a_row += 1
			if r.player_id == player_id:
				pos = count
				break
			previousrank = r
		session.close()
		return pos

	def AccessCheck( self, ladder_id, username, role ):
		session = self.sessionmaker()
		try:
			player_query = session.query( Player ).filter( Player.nick == username )
			if player_query.count () == 0:
				self.AddPlayer( username, Roles.User )
				player_query = session.query( Player ).filter( Player.nick == username )
			is_superadmin = player_query.filter( Player.role >= Roles.GlobalAdmin ).count() == 1
			if role == Roles.LadderAdmin:
				if ladder_id != -1:
					is_ladderadmin = session.query( Option ).filter( Option.ladder_id == ladder_id ).filter( Option.key == Option.adminkey ) \
						.filter( Option.is_whitelist == True).filter( Option.value == username ).count() >= 1
					session.close()
					return is_superadmin or is_ladderadmin
				else:
					is_ladderadmin = session.query( Option ).filter( Option.key == Option.adminkey ) \
						.filter( Option.is_whitelist == True).filter( Option.value == username ).count() >= 1
					session.close()
					return is_superadmin or is_ladderadmin
			player = player_query.first()
			if player:
				is_global_banned = player.role == Roles.GlobalBanned
				is_banned = 0 < session.query( Bans ).filter( Bans.player_id == player.id ).filter( Bans.ladder_id == ladder_id ).filter( Bans.end >= datetime.datetime.now() ).count()
				if is_banned:
					session.close()
					return False
				session.close()
				return player.role >= role or is_superadmin
			session.close()
			return False
		except exc.DBAPIError, e:
			trace = traceback.format_exc()
			Log.Error( trace, '[LadderDB Exception]' )
			raise DbConnectionLostException(trace)

	def AddLadderAdmin( self, ladder_id, username ):
		self.AddOption( ladder_id, True, Option.adminkey, username )

	def DeleteLadderAdmin( self, ladder_id, username ):
		self.DeleteOption(  ladder_id, True, Option.adminkey, username )

	def AddGlobalAdmin( self, username ):
		session = self.sessionmaker()
		player = session.query( Player ).filter( Player.nick == username ).first()
		if not player:
			self.AddPlayer( username, Roles.GlobalAdmin )
		else:
			player.role = Roles.GlobalAdmin
			session.add(player)
			session.commit()
		session.close()

	def DeleteGlobalAdmin( self, username ):
		session = self.sessionmaker()
		player = session.query( Player ).filter( Player.nick == username ).first()
		if not player:
			session.close()
			return
		else:
			player.role = Roles.User
			session.add(player)
			session.commit()
		session.close()

	def SetLadderRankingAlgo( self, ladder_id, algoname ):
		ladder = self.GetLadder( ladder_id )
		if ladder.ranking_algo_id != algoname:
			session = self.sessionmaker()
			ladder.ranking_algo_id = algoname
			algo_instance = GlobalRankingAlgoSelector.GetInstance( ladder.ranking_algo_id )
			entityType = algo_instance.GetDbEntityType()
			ranks = session.query( entityType ).filter( entityType.ladder_id == ladder_id )
			for r in ranks:
				session.delete( r )
			session.add( ladder )
			session.commit()
			session.close()
			self.RecalcRankings( ladder_id )

	def GetAvgMatchDelta( self, ladder_id ):
		ladder = self.GetLadder( ladder_id )
		if ladder.match_average_count == 0:
			return 1
		return ladder.match_average_sum / ladder.match_average_count

	def UpdateAvgMatchDelta( self, ladder_id, player_delta ):
		if player_delta == 0:
			return
		ladder = self.GetLadder( ladder_id )
		session = self.sessionmaker()
		ladder.match_average_sum += player_delta
		ladder.match_average_count += 1
		session.add( ladder )
		session.commit()
		session.close()

	def RecalcRankings( self, ladder_id ):
		session = self.sessionmaker()
		ladder = self.GetLadder( ladder_id )
		ladder.match_average_sum = 0
		ladder.match_average_count = 0
		session.add( ladder )
		algo_instance = GlobalRankingAlgoSelector.GetInstance( ladder.ranking_algo_id )
		entityType = algo_instance.GetDbEntityType()
		ranks = session.query( entityType ).filter( entityType.ladder_id == ladder_id )
		for r in ranks:
			session.delete( r )
		session.commit()
		for m in session.query(Match).filter(Match.ladder_id == ladder_id ).order_by(Match.date.asc()):
			algo_instance.Update( ladder_id, m, self)
		session.close()

	def GetMatches( self, ladder_id, order=Match.date.desc() ):
		session = self.sessionmaker()
		matches = session.query( Match ).filter( Match.ladder_id == ladder_id ).order_by( order )
		session.close()
		if matches.count() < 1:
			raise ElementNotFoundException( "no matches for ladder id %s found"%str(ladder_id) )
		return matches.all()

	def DeleteMatch( self, ladder_id, match_id ):
		session = self.sessionmaker()
		ladder = self.GetLadder( ladder_id )
		match = session.query( Match ).filter( Match.id == match_id ).first()
		if match:
			for r in match.results:
				session.delete( r )
				session.commit()
			for s in match.settings:
				session.delete( s )
				session.commit()
			session.delete( match )
			session.commit()
			session.close()
		else:
			session.close()
			raise ElementNotFoundException( Match(  ) )
		self.RecalcRankings( ladder_id )

	def BanPlayer( self, ladder_id, username, banlength=None ):
		session = self.sessionmaker()
		player = self.GetPlayer( username )
		ban = Bans( )
		ban.player_id = player.id
		if not banlength:
			ban.end = datetime.date.max
		else:
			try:
				ban.end = datetime.datetime.now() + banlength
			except OverflowError:
				ban.end = datetime.date.max
		ban.ladder_id = ladder_id
		session.add( ban )
		session.commit()
		session.close()

	def UnbanPlayer( self, username, ladder_id=-1, just_expire=True ):
		session = self.sessionmaker()
		player = self.GetPlayer( username )
		bans = session.query( Bans ).filter( Bans.player_id == player.id ).filter( Bans.ladder_id == ladder_id ).all()
		for b in bans:
			if just_expire:
				b.end = datetime.datetime.now()
				session.add( b )
			else:
				session.delete( b )
			session.commit()
		session.close()


	def GetBansPerLadder( self, ladder_id ):
		session = self.sessionmaker()
		if ladder_id == -1:
			bans = session.query( Bans ).filter( Bans.end >= datetime.datetime.now() ).all()
		else:
			bans = session.query( Bans ).filter( Bans.end >= datetime.datetime.now() ).filter( Bans.ladder_id == ladder_id ).all()
		session.close()
		return bans

	def GetBansPerPlayer( self, player_id ):
		session = self.sessionmaker()
		bans = session.query( Bans ).filter( Bans.player_id == player_id ).all()
		session.close()
		return bans

	def GetDBRevision(self):
		session = self.sessionmaker()
		rev = session.query( Config.dbrevision ).order_by( Config.dbrevision.desc() ).first()
		if not rev:
			#default value
			rev = -1
		else:
			rev = rev[0]
		session.close()
		return rev

	def SetDBRevision(self,rev):
		session = self.sessionmaker()
		conf = session.query( Config ).first()
		if not conf:
			#default value
			conf = Config()
		conf.dbrevision = rev
		session.add( conf )
		session.commit()
		session.close()

	def UpdateDBScheme( self, oldrev, current_db_rev ):
		session = self.sessionmaker()
		if current_db_rev > oldrev:
			if oldrev == -1:
				results = session.query( Result ).all()
				for r in results:
					r.quit = False
					r.kicked = False
					r.timeout = False
					session.add( r )
			if oldrev < 4:
				try:
					for p in session.query( Player ).all():
						p.server_id = -1
						session.add( p )
				except:
					print "execute: ALTER TABLE players ADD server_id int\n" * 67
					exit(-1)

		session.commit()
		session.close()

	def GetLadderByPlayer( self, player_id ):
		session = self.sessionmaker()
		ret = session.query( Ladder ).filter( Ladder.id.in_( session.query( Result.ladder_id ).\
			filter( Result.player_id == player_id ) ) ).order_by( Ladder.id )
		session.close()
		if ret.count() > 0:
			return ret.all()
		else:
			return []

	def MergeAccounts( self, from_nick, to_nick, override_conflict = False ):
		session = self.sessionmaker()
		from_player = self.GetPlayer( from_nick )
		to_player = self.GetPlayer( to_nick )
		from_results = session.query( Result ).filter( Result.player_id == from_player.id )
		conflicts = []
		recalc_ladders = []
		result = "merge sucessful, no conficts detected"
		for from_result in from_results:
			if not from_result.ladder_id in recalc_ladders:
				recalc_ladders.append(from_result.ladder_id)
			if session.query( Result.id ).filter( Result.match_id == from_result.match_id ).filter( Result.player_id == to_player.id ).count() == 0:
				#no conflicting result present
				from_result.player_id = to_player.id
				session.add( from_result )
			else:
				#conflicting
				conflicts.append( from_result )

		if len( conflicts ) != 0:
		 	if override_conflict:
				result = "merge successful, the following matches have been automatically deleted since they contained conflicts:\n"
				for result_table in conflicts:
					match = session.query( Match ).filter( Match.id == result_table.match_id ).first()
					laddername = session.query( Ladder ).filter( Ladder.id == match.ladder_id ).first()
					result += "#%d (%s) ladder: %s (%d)\n" % (match.id, match.date, laddername, match.ladder_id)
					#delete the match
					for r in match.results:
						session.delete( r )
						session.commit()
					for s in match.settings:
						session.delete( s )
						session.commit()
					session.delete( match )
			else:
				result = "merge failed: conflicts existing, please resolve them manually or use the override switch to automatically delete them; conflicting matches:\n"
				for match in conflicts:
					laddername = session.query( Ladder ).filter( Ladder.id == match.ladder_id ).first()
					result += "#%d (%s) ladder: %s (%d)\n" % (match.match_id, match.date, laddername, match.ladder_id)
		session.commit()
		session.close()
		if len(conflicts) == 0 or override_conflict: # no conflicts or conflicts autoresolved: recalc ranks and ban the o
			for ladderid in recalc_ladders: # recalculate ladders which changed
				self.RecalcRankings( ladderid )
			self.BanPlayer( -1, from_nick )
		return result

	def GetRankAndPositionInfo(self, players, ladder_id ):
		session = self.sessionmaker()
		ladder = self.GetLadder( ladder_id )
		res = dict()
		for player in session.query( Player ).filter( Player.nick.in_(players) ):
			aloginstance = GlobalRankingAlgoSelector.GetInstance( ladder.ranking_algo_id )
			algoname = aloginstance.__class__.__name__
			entityType = aloginstance.GetDbEntityType()
			rank = session.query( entityType ).filter( entityType.ladder_id == ladder.id ).filter(entityType.player_id == player.id).first()
			pos = self.GetPlayerPosition( ladder_id, player.id )
			if rank:
				res[player.nick] = ( ( rank, pos, entityType ) )
		session.close()
		return res

	def SetPassword( self, nick, password ):
		session = self.sessionmaker()
		try:
			player = self.GetPlayer( nick )
			player.SetPassword( password )
			#print "%s: %s"%(nick,player.pwhash)
			session.add( player )
			session.commit()
			session.close()
			return True
		except ElementNotFoundException, e:
			pass
		session.close()
		return False
	