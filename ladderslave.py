# -*- coding: utf-8 -*-
from customlog import *
from ParseConfig import *
import commands, thread, signal, os, time, subprocess, traceback, platform, sys
import replay_upload
from db_entities import *
from ladderdb import *
from match import *
from ranking import GlobalRankingAlgoSelector
if platform.system() == "Windows":
	import win32api

from utilities import *

bstr_nonneg = lambda n: n>0 and bstr_nonneg(n>>1).lstrip('0')+str(n&1) or '0'

"""
	*  b0 = undefined (reserved for future use)
	* b1 = ready (0=not ready, 1=ready)
	* b2..b5 = team no. (from 0 to 15. b2 is LSB, b5 is MSB)
	* b6..b9 = ally team no. (from 0 to 15. b6 is LSB, b9 is MSB)
	* b10 = mode (0 = spectator, 1 = normal player)
	* b11..b17 = handicap (7-bit number. Must be in range 0..100). Note: Only host can change handicap values of the players in the battle (with HANDICAP command). These 7 bits are always ignored in this command. They can only be changed using HANDICAP command.
	* b18..b21 = reserved for future use (with pre 0.71 versions these bits were used for team color index)
	* b22..b23 = sync status (0 = unknown, 1 = synced, 2 = unsynced)
	* b24..b27 = side (e.g.: arm, core, tll, ... Side index can be between 0 and 15, inclusive)
	* b28..b31 = undefined (reserved for future use)
"""

class BattleStatus:
	def __init__(self, status, nick ):
		status = int(status)
		self.team = getteam(status)
		self.ally = getally(status)
		self.side = getside(status)
		self.spec = getspec(status)
		self.nick = nick
		self.decimal = int(status)

	def __str__(self):
		return "nick: %s -- team:%d ally:%d side:%d spec:%d decimal:%d"%(self.nick,self.team,self.ally,self.side,self.spec,self.decimal)

import helpstrings
helpstring_user = helpstrings.helpstring_user_slave

def sendstatus(self, socket ):
	if self.ingame:
		socket.send("MYSTATUS 1\n")
	else:
		socket.send("MYSTATUS 0\n")

class Main:
	sock = 0
	battleowner = ""
	battleid = -1
	script = ""
	ingame = False
	gamestarted = False
	joinedbattle = False
	toshutdown = False
	ladderid = -1
	if platform.system() == "Windows":
		scriptbasepath = os.environ['USERPROFILE']
	else:
		scriptbasepath = os.environ['HOME']
	battleusers = dict()
	battleoptions = dict()
	ladderlist = dict()
	battle_statusmap = dict()
	teams = dict()
	allies = dict()
	bots = dict()
	disabledunits = dict()
	battlefounder = ""
	hostip = ""
	hostport = 0
	def startspring(self,socket,g):
		currentworkingdir = os.getcwd()
		try:
			players = []
			for player in self.battle_statusmap:
				status = self.battle_statusmap[player]
				if not status.spec and player != self.app.config["nick"]:
					players.append(player)
			pregame_rankinfo = self.db.GetRankAndPositionInfo( players, self.ladderid )
			
			if self.ingame == True:
				self.saybattle( self.socket, self.battleid, "Error: game is already running")
				return
			self.output = ""
			self.ingame = True
			doSubmit = self.ladderid != -1 and self.db.LadderExists( self.ladderid ) and self.CheckValidSetup(self.ladderid,False,0)
			if doSubmit:
				self.saybattleex(socket, self.battleid, "will submit the result to the ladder")
			else:
				self.saybattleex(socket, self.battleid, "won't submit the result to the ladder")
			sendstatus( self, socket )
			st = time.time()
			self.log.Info("*** Starting spring: command line \"%s %s\"" % (self.app.config["springdedclientpath"], os.path.join(self.scriptbasepath,"%f.txt" % g )) )
			if platform.system() == "Windows":
				dedpath = "\\".join(self.app.config["springdedclientpath"].replace("/","\\").split("\\")[:self.app.config["springdedclientpath"].replace("/","\\").count("\\")])
				if not dedpath in sys.path:
					sys.path.append(dedpath)
			if "springdatapath" in self.app.config:
				springdatapath = self.app.config["springdatapath"]
				if not springdatapath in sys.path:
					sys.path.append(springdatapath)
				os.chdir(springdatapath)
			else:
				springdatapath = None
			if springdatapath!= None:
				os.environ['SPRING_DATADIR'] = springdatapath
			self.pr = subprocess.Popen((self.app.config["springdedclientpath"],os.path.join(self.scriptbasepath,"%f.txt" % g )),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,cwd=springdatapath)
			l = self.pr.stdout.readline()
			while len(l) > 0:
				self.output += l
				l = self.pr.stdout.readline()
			status = self.pr.wait()
			et = time.time()
			if status != 0:
				self.saybattle( self.socket,self.battleid,"Error: Spring exited with status %i" % status)
				self.log.Error( "Error: Spring exited with status %i" % status )
				self.log.Error( self.output )
			if doSubmit:
				matchid = -1
				try:
					mr = AutomaticMatchToDbWrapper( self.output, self.ladderid )
					matchid = self.db.ReportMatch( mr, True )
					postgame_rankinfo = self.db.GetRankAndPositionInfo( players, self.ladderid )
					news_string = '\n'.join( self.GetRankInfoDifference( pregame_rankinfo, postgame_rankinfo ) )
					#self.saybattle( self.socket, self.battleid, news_string )
					self.saybattleex(self.socket, self.battleid, "has submitted the score update to the ladder: http://ladder.springrts.com/viewmatch.py?id=%d"%matchid)
				except:
					exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
					self.log.Error( 'EXCEPTION: BEGIN\n%s\nEXCEPTION: END\nCLIENTLOG: BEGIN\n%s\nCLIENTLOG: END'%(exc,self.output) )
					self.saybattleex(self.socket, self.battleid, "could not submit ladder score updates")
				if matchid != -1:
					reply = replay_upload.postReplay( os.getcwd() + "/"+ self.db.GetMatchReplay( matchid ), 'LadderBot', "Ladder: %s, Match #%d" % ( self.db.GetLadderName(self.ladderid), matchid ) )
					replaysiteok = reply.split()[0] == 'SUCCESS'
					if replaysiteok:
						self.saybattleex(self.socket, self.battleid, reply.split()[1] )
					else:
						self.saybattleex(self.socket, self.battleid, "error uploading replay to http://replays.adune.nl")

		except:
			exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
			self.log.Error( 'EXCEPTION: BEGIN\n%s\nEXCEPTION: END'%exc )
		try:
			os.remove(os.path.join(self.scriptbasepath,"%f.txt" % g))
		except:
			pass
		os.chdir(currentworkingdir)
		self.ingame = False
		sendstatus( self, socket )
		if self.toshutdown:
			self.KillBot()

	def KillBot(self):
		if platform.system() == "Windows":
			handle = win32api.OpenProcess(1, 0, os.getpid())
			win32api.TerminateProcess(handle, 0)
		else:
			os.kill(os.getpid(),signal.SIGKILL)

	def CheckValidSetup( self, ladderid, echoerrors, socket ):
		a = self.CheckvalidPlayerSetup(ladderid,echoerrors,socket)
		b = self.CheckValidOptionsSetup(ladderid,echoerrors,socket)
		return a and b

	def CheckvalidPlayerSetup( self, ladderid, echoerrors, socket ):
		IsOk = True
		laddername = self.db.GetLadderName( ladderid )
		teamcount = len(self.teams)
		allycount = len(self.allies)
		botcount = len(self.bots)

		bannedplayers = ""
		duplicatebots = ""
		checkedbots = []
		for player in self.battle_statusmap:
			if not self.db.AccessCheck( ladderid, player, Roles.User ):
				IsOk = False
				bannedplayers += " " + player
			if player in self.bots: # it's a bot
				botlib = self.bots[player]
				if not botlib in checkedbots:
					checkedbots.append(botlib)
				else:
					IsOk = False
					duplicatebots += " " + player
		if not len(bannedplayers) == 0 and echoerrors:
			self.saybattle( socket, self.battleid, "There are banned player for " + laddername  + " (" + bannedplayers + " )" )
		if not len(duplicatebots) == 0 and echoerrors:
			self.saybattle( socket, self.battleid, "There are too many bots of the same type (" + duplicatebots + " )" )

		minbotcount = self.db.GetLadderOption( ladderid, "min_ai_count" )
		maxbotcount = self.db.GetLadderOption( ladderid, "max_ai_count" )
		minteamcount = self.db.GetLadderOption( ladderid, "min_team_count" )
		maxteamcount = self.db.GetLadderOption( ladderid, "max_team_count" )
		minallycount = self.db.GetLadderOption( ladderid, "min_ally_count" )
		maxallycount = self.db.GetLadderOption( ladderid, "max_ally_count" )
		if botcount < minbotcount:
			if echoerrors:
				self.saybattle( socket, self.battleid, "There are too few AIs for " + laddername  + " (" + str(botcount) + ")" )
			IsOk =  False
		if botcount > maxbotcount:
			if echoerrors:
				self.saybattle( socket, self.battleid, "There are too many AIs for " + laddername + " (" + str(botcount) + ")" )
			IsOk = False
		if teamcount < minteamcount:
			if echoerrors:
				self.saybattle( socket, self.battleid, "There are too few control teams for " + laddername  + " (" + str(teamcount) + ")" )
			IsOk =  False
		if teamcount > maxteamcount:
			if echoerrors:
				self.saybattle( socket, self.battleid, "There are too many control teams for " + laddername + " (" + str(teamcount) + ")" )
			IsOk = False
		if allycount < minallycount:
			if echoerrors:
				self.saybattle( socket, self.battleid, "There are too few allies for " + laddername  + " (" + str(allycount) + ")" )
			IsOk = False
		if allycount > maxallycount:
			if echoerrors:
				self.saybattle( socket, self.battleid, "There are too few allies for " + laddername  + " (" + str(allycount) + ")" )
			IsOk = False
		minteamsize = self.db.GetLadderOption( ladderid, "min_team_size" )
		maxteamsize = self.db.GetLadderOption( ladderid, "max_team_size" )
		minallysize = self.db.GetLadderOption( ladderid, "min_ally_size" )
		maxallysize = self.db.GetLadderOption( ladderid, "max_ally_size" )
		teamsizesok = True
		errorstring = "The following control teams have too few players in them for " + laddername + ":\n"
		for team in self.teams:
			teamsize = self.teams[team]
			if teamsize < minteamsize:
				errorstring += str(team) + "=" + str(teamsize) + " "
				teamsizesok = False
				IsOk = False
		if not teamsizesok and echoerrors:
			self.saybattle( socket, self.battleid, errorstring )
		teamsizesok = True
		errorstring = "The following control teams have too many players in them for " + laddername + ":\n"
		for team in self.teams:
			if teamsize > maxteamsize:
				IsOk = False
				errorstring += str(team) + "=" + str(teamsize) + " "
				teamsizesok = False
		if not teamsizesok and echoerrors:
			self.saybattle( socket, self.battleid, errorstring )
		allysizesok = True
		errorstring = "The following ally have too few players in them for " + laddername + ":\n"
		for ally in self.allies:
			allysize = self.allies[ally]
			if allysize < minallysize:
				IsOk = False
				allysizesok = False
				errorstring += str(team) + "=" + str(teamsize) + " "
		if not allysizesok and echoerrors:
			self.saybattle( socket, self.battleid, errorstring )
		allysizesok = True
		errorstring = "The following ally have too many players in them for " + laddername + ":\n"
		for ally in self.allies:
			allysize = self.allies[ally]
			if allysize > maxallysize:
				IsOk = False
				allysizesok = False
				errorstring += str(team) + "=" + str(teamsize) + " "
		if not allysizesok and echoerrors:
			self.saybattle( socket, self.battleid, errorstring )
		return IsOk


	def CheckValidOptionsSetup( self, ladderid, echoerrors, socket ):
		IsOk = True
		laddername = self.db.GetLadderName( ladderid )
		for key in self.battleoptions:
			value = self.battleoptions[key]
			OptionOk = self.CheckOptionOk( ladderid, key, value )
			if not OptionOk:
				if IsOk and echoerrors:
					self.saybattle( socket, self.battleid, "The following settings are not compatible with " + laddername + ":" )
				IsOk = False
				if echoerrors:
					self.saybattle( socket, self.battleid, key + "=" + value )
		return IsOk

	def CheckOptionOk( self, ladderid, keyname, value ):
		if self.db.GetOptionKeyValueExists( ladderid, False, keyname, value ): # option in the blacklist
			return False
		if self.db.GetOptionKeyExists( ladderid, True, keyname ): # whitelist not empty
			return self.db.GetOptionKeyValueExists( ladderid, True, keyname, value )
		else:
			return True

	def JoinGame(self,s):
		if self.joinedbattle:
			sendstatus( self, self.socket )
			if not self.gamestarted:
				return
			if self.ingame:
				return
			#start spring
			g = time.time()
			if platform.system() == "Linux":
				f = open(os.path.join(os.environ['HOME'],"%f.txt" % g),"a")
			else:
				f = open(os.path.join(os.environ['USERPROFILE'],"%f.txt" % g),"a")
			self.script = "[GAME]\n{"
			self.script += "\n\tHostIP=" + self.hostip + ";"
			self.script += "\n\tHostPort=" + self.hostport + ";"
			self.script += "\n\tIsHost=0;"
			self.script += "\n\tMyPlayerName=" + self.app.config["nick"] + ";"
			self.script += "\n}"
			f.write(self.script)
			f.close()
			thread.start_new_thread(self.startspring,(s,g))

	def onload(self,tasc):
		self.app = tasc.main
		self.tsc = tasc
		self.hosttime = time.time()
		self.battleid = int(self.app.config["battleid"])
		self.ladderid = int(self.app.config["ladderid"])
		self.battlepassword = self.app.config["battlepassword"]
		self.log = CLog()
		self.log.Init( self.app.config['nick']+'.log', self.app.config['nick']+'.err' )
		self.db = LadderDB( parselist(self.app.config["alchemy-uri"],",")[0], [], parselist(self.app.config["alchemy-verbose"],",")[0] )

	def oncommandfromserver(self,command,args,s):
		#print "From server: %s | Args : %s" % (command,str(args))
		self.socket = s
		if command == "JOINBATTLE":
			self.joinedbattle = True
			good( "Joined battle: " + str(self.battleid) )
		if command == "JOINBATTLEFAILED":
			self.joinedbattle = False
			bad( "Join battle failed, ID: " + str(self.battleid) + " reason: " + " ".join(args[0:] ) )
			self.KillBot()
		if command == "FORCEQUITBATTLE":
			self.joinedbattle = False
			bad( "Kicked from battle: " + str(self.battleid) )
			self.toshutdown = True
			if not self.ingame:
				self.KillBot()
		if command == "BATTLECLOSED" and len(args) == 1 and int(args[0]) == self.battleid:
			self.joinedbattle = False
			notice( "Battle closed: " + str(self.battleid) )
			self.toshutdown = True
			if not self.ingame:
				self.KillBot()
		if command == "ENABLEALLUNITS":
			self.disabledunits = dict()
		if command == "ENABLEUNITS" and len(args) > 1:
			for unit in args[1:]:
				del self.disabledunits[unit]
		if command == "DISABLEUNITS":
			for unit in args[1:]:
				self.disabledunits[unit] = 0
		if command == "SETSCRIPTTAGS":
			for option in args[0].split():
				pieces = parselist( option, "=" )
				if len(pieces) != 2:
					error( "parsing error of option string: " + option )
				key = pieces[0]
				if key.startswith("/game/"): # strip prefix
					key = key[6:]
				elif key.startswith("game/"):#  strip prefix
					key = key[5:]
				if key.startswith("restrict/"):
					unitname = key[9:]
					self.disabledunits[unitname] = int(value)
				value = pieces[1]
				self.battleoptions[key] = value
		if command == "REQUESTBATTLESTATUS":
			self.socket.send( "MYBATTLESTATUS 4194816 255\n" )#spectator+synced/white
		if command == "SAIDBATTLE" and len(args) > 1 and args[1].startswith("!"):
			who = args[0]
			command = args[1]
			args = args[2:]

			if len(command) > 0 and command[0] == "!":
				if not self.db.AccessCheck( -1, who, Roles.User ):
					self.sayPermissionDenied( self.socket, who, command )
					#log
					return
			else:
				return

			try:
				if self.battle_statusmap[who].spec and who != self.battlefounder and not self.db.AccessCheck( -1, who, Roles.LadderAdmin ):
					return
			except:
				pass

			if command == "!ladderchecksetup":
				ladderid = self.ladderid
				if len(args) == 1 and args[0].isdigit():
					ladderid = int(args[0])
				if ladderid == -1:
					self.saybattle( self.socket, self.battleid,"No ladder has been enabled.")
				elif self.db.LadderExists( ladderid ):
					laddername = self.db.GetLadderName( ladderid )
					if self.CheckValidSetup( ladderid, True, self.socket ):
						self.saybattle( self.socket, self.battleid, "All settings are compatible with the ladder " + laddername )
				else:
					self.saybattle( self.socket, self.battleid,"Invalid ladder ID.")
			if command == "!ladderlist":
				self.saybattle( self.socket, self.battleid, "Available ladders, format name: ID:" )
				for l in self.db.GetLadderList(Ladder.name):
					self.saybattle( self.socket, self.battleid, "%s: %d" %(l.name, l.id ) )
			if command == "!ladder":
				if len(args) == 1 and args[0].isdigit():
					ladderid = int(args[0])
					if ladderid != -1:
						if self.db.LadderExists( ladderid ):
							laddername = self.db.GetLadderName( ladderid )
							self.saybattle( self.socket, self.battleid,"Enabled ladder reporting for ladder: " + laddername )
							self.ladderid = ladderid
							if self.CheckValidSetup( ladderid, True, self.socket ):
								self.saybattle( self.socket, self.battleid, "All settings are compatible with the ladder " + laddername )
						else:
							self.saybattle( self.socket, self.battleid,"Invalid ladder ID.")
					else:
						self.ladderid = ladderid
						self.saybattle( self.socket, self.battleid,"Ladder reporting disabled.")
				else:
					self.saybattle( self.socket, self.battleid,"Invalid command syntax, check !ladderhelp for usage.")
			if command == "!ladderleave":
				self.joinedbattle = False
				good( "Leaving battle: " + str(self.battleid) )
				self.socket.send("LEAVEBATTLE\n")
				self.toshutdown = True
				if not self.ingame:
					self.KillBot()
			if command == "!ladderhelp":
				self.saybattle( self.socket, self.battleid,  "Hello, I am a bot to manage and keep stats of ladder games.\nYou can use the following commands:")
				self.saybattle( self.socket, self.battleid, helpstring_user )
			if command == '!ladderdebug':
				if not self.db.AccessCheck( self.ladderid, who, Roles.Owner ):
					self.sayPermissionDenied( self.socket, who, command )
					#log
					return
				import fakeoutput
				if len(args) > 0 and args[0].isdigit():
					idx = max( int(args[0]), len(fakeoutput.fakeoutput) -1 )
					output = fakeoutput.fakeoutput[idx]
				else:
					output = fakeoutput.fakeoutput[-1]
				upd = GlobalRankingAlgoSelector.GetPrintableRepresentation( self.db.GetRanks( self.ladderid ), self.db )
				players = ['doofus', 'idiot']
				pregame_rankinfo = self.db.GetRankAndPositionInfo( players, self.ladderid )
				self.saybattle( self.socket, self.battleid, 'before:\n' + upd )
				try:
					mr = AutomaticMatchToDbWrapper( output, self.ladderid )
					repeats = int(args[1]) if len(args) > 1 else 1
					for i in range(repeats):
						self.db.ReportMatch( mr, False )#false skips validation check of output against ladder rules
					upd = GlobalRankingAlgoSelector.GetPrintableRepresentation( self.db.GetRanks( self.ladderid ), self.db )
					self.saybattle( self.socket, self.battleid, 'pre-recalc:\n' +upd )
					self.db.RecalcRankings(self.ladderid)
				except InvalidOptionSetup, e:
					self.saybattle( self.socket, self.battleid, str(e) )
					return

				upd = GlobalRankingAlgoSelector.GetPrintableRepresentation( self.db.GetRanks( self.ladderid ), self.db )
				self.saybattle( self.socket, self.battleid, 'after:\n' +upd )
				postgame_rankinfo = self.db.GetRankAndPositionInfo( players, self.ladderid )
				self.saybattle( self.socket, self.battleid, '\n'.join( self.GetRankInfoDifference( pregame_rankinfo, postgame_rankinfo ) ) )

			if command == "!ladderforcestart":
				if not self.db.AccessCheck( self.ladderid, who, Roles.User ):
					self.sayPermissionDenied( self.socket, who, command )
					#log
					return
				self.JoinGame(s)

			if command == '!ladderstress':
				if not self.db.AccessCheck( self.ladderid, who, Roles.Owner ):
					self.sayPermissionDenied( self.socket, who, command )
					#log
					return
				import fakeoutput
				if len(args) > 0 and args[0].isdigit():
					idx = max( int(args[0]), len(fakeoutput.fakeoutput) -1 )
					output = fakeoutput.fakeoutput[idx]
				else:
					output = fakeoutput.fakeoutput[-1]
				if len(args) > 1 and args[1].isdigit():
					times = int(args[1])
				else:
					times = 1

				now = datetime.datetime.now()
				upd = GlobalRankingAlgoSelector.GetPrintableRepresentation( self.db.GetRanks( self.ladderid ), self.db )
				for i in range ( times ):
					try:
						mr = AutomaticMatchToDbWrapper( output, self.ladderid )
						repeats = int(args[1]) if len(args) > 1 else 1
						for i in range(repeats):
							self.db.ReportMatch( mr, False )#false skips validation check of output against ladder rules
						upd = GlobalRankingAlgoSelector.GetPrintableRepresentation( self.db.GetRanks( self.ladderid ), self.db )
						self.db.RecalcRankings(self.ladderid)
					except InvalidOptionSetup, e:
						self.saybattle( self.socket, self.battleid, str(e) )
						return
				upd = GlobalRankingAlgoSelector.GetPrintableRepresentation( self.db.GetRanks( self.ladderid ), self.db )
				self.saybattle( self.socket, self.battleid, '%i recalcs took %s:\n'%(times, str(datetime.datetime.now() - now) ))

			if command == "!ladderreportgame":
				if len(args) < 2:
					self.saybattle( self.socket, self.battleid, "Invalid command syntax (too few args), check !ladderhelp for usage." )
				else:
					ladderid = self.ladderid
					try:
						if not self.db.AccessCheck( ladderid, who, Roles.LadderAdmin ):
							self.sayPermissionDenied( self.socket, who, command )
							#log
							return
						ladder = self.db.GetLadder( ladderid )
						usercounter = 0
						userresults = dict()
						while ( usercounter != len(args) ):
							username, equal, result = args[usercounter].partition("=")
							if ( len(result) == 0 ):
								self.saybattle( self.socket, self.battleid, "Invalid command syntax, check !ladderhelp for usage." )
								return
							userresults[username] = int(result)
							usercounter = usercounter +1

						if  not self.CheckvalidPlayerSetup( ladderid, True , self.socket ):
							self.saybattle( self.socket, self.battleid, "Invalid setup" )
						players = []
						teams_map = dict()
						allies_map = dict()
						for player in self.battle_statusmap:
							status = self.battle_statusmap[player]
							if not status.spec and player != self.app.config["nick"]:
								players.append(player)
								teams_map[player] = status.team
								allies_map[player] = status.ally
						mr = ManualMatchToDbWrapper( players, userresults, self.teams, ladderid, self.battleoptions, self.disabledunits, self.bots, self.allies, teams_map, allies_map )
						try:
							self.db.ReportMatch( mr )
							self.saybattleex(self.socket, self.battleid, "has submitted ladder score updates")
						except BannedPlayersDetectedException, b:
							self.saybattle( self.socket,self.battleid,str(b) )
							self.log.Error( b, 'BannedPlayersDetectedException' )
						except Exception, e:
							self.saybattle( self.socket,self.battleid,"There was an error reporting the battle outcome: %s"%str(e) )
							self.log.Error( e, 'Exception' )

					except ElementNotFoundException, e:
						self.saybattle( self.socket,self.battleid, "Invalid ladder ID." )
						self.log.Error( e, 'ElementNotFoundException' )
			if command == "!ladderlistoptions":
				if len(args) != 1 or not args[0].isdigit():
					ladderid =  self.ladderid
				else:
					ladderid = int(args[0])
					if self.db.LadderExists( ladderid ):
						self.saybattle( self.socket,self.battleid, "Ladder: " + self.db.GetLadderName(ladderid) )
						self.saybattle( self.socket,self.battleid, "Min AIs in a Match ( how many AIs ): " + str(self.db.GetLadderOption( ladderid, "min_ai_count" )) )
						self.saybattle( self.socket,self.battleid, "Max Ais in a Match ( how many AIs ): " + str(self.db.GetLadderOption( ladderid, "max_ai_count" )) )
						self.saybattle( self.socket,self.battleid, "Min Players in a Team ( sharing control ): " + str(self.db.GetLadderOption( ladderid, "min_team_size" )) )
						self.saybattle( self.socket,self.battleid, "Max Players in a Team ( sharing control ): " + str(self.db.GetLadderOption( ladderid, "max_team_size" )) )
						self.saybattle( self.socket,self.battleid, "Min Teams in an Ally ( being allied ): " + str(self.db.GetLadderOption( ladderid, "min_ally_size" )) )
						self.saybattle( self.socket,self.battleid, "Max Teams in an Ally ( being allied ): " + str(self.db.GetLadderOption( ladderid, "max_ally_size" )) )
						self.saybattle( self.socket,self.battleid, "Min Teams in a Match ( how many Teams ): " + str(self.db.GetLadderOption( ladderid, "min_team_count" )) )
						self.saybattle( self.socket,self.battleid, "Max Teams in a Match ( how many Teams ): " + str(self.db.GetLadderOption( ladderid, "max_team_count" )) )
						self.saybattle( self.socket,self.battleid, "Min Alliances in a Match ( how many Allys ): " + str(self.db.GetLadderOption( ladderid, "min_ally_count" )) )
						self.saybattle( self.socket,self.battleid, "Max Alliances in a Match ( how many Allys ): " + str(self.db.GetLadderOption( ladderid, "max_ally_count" )) )
						self.saybattle( self.socket,self.battleid, "Whitelisted options ( if a key is present, no other value except for those listed will be allowed for such key ):" )
						for opt in self.db.GetFilteredOptions( ladderid, True ):
							self.saybattle( self.socket,self.battleid, opt.key + ": " + opt.value )
						self.saybattle( self.socket,self.battleid, "Blacklisted options ( if a value is present for a key, such value won't be allowed ):" )
						for opt in self.db.GetFilteredOptions( ladderid, False ):
							self.saybattle( self.socket,self.battleid, opt.key + ": " + opt.value )
					else:
						self.saybattle( self.socket,self.battleid, "Invalid ladder ID." )

			if command == "!score":
				if not self.db.AccessCheck( -1, who, Roles.User ):
					self.sayPermissionDenied( self.socket, who, command )
					#log
					return
				if len(args) > 2:
					self.saybattle( self.socket,self.battleid, "Invalid command syntax, check !ladderhelp for usage." )
				else:
					ladderid = self.ladderid
					playername = ""
					rep = ''
					if len(args) > 0:
						if args[0].isdigit():
							ladderid = int(args[0])
							if len(args) > 1:
								playername = args[1]
						else:
							playername = args[0]
					if ladderid != -1 and len(playername) == 0:
						rep = GlobalRankingAlgoSelector.GetPrintableRepresentation( self.db.GetRanks( ladderid ), self.db )
					elif ladderid != -1 and len(playername) != 0:
						rep = GlobalRankingAlgoSelector.GetPrintableRepresentation( self.db.GetRanks( ladderid, playername ), self.db )
					elif ladderid == -1 and len(playername) != 0:
						rep = GlobalRankingAlgoSelector.GetPrintableRepresentationPlayer( self.db.GetPlayerRanks( playername ), self.db )
					self.saybattle( self.socket,self.battleid, rep )
			if command == "!ladderopponent":
				if len(args) > 1:
					self.saybattle( self.socket,self.battleid, "Invalid command syntax, check !ladderhelp for usage." )
					return
				if len(args) == 1:
					ladderid = int(args[0])
				else:
					ladderid = self.ladderid
				if not self.db.AccessCheck( ladderid, who, Roles.User ):
					self.sayPermissionDenied( self.socket, who, command )
					#log
					return
				if not self.db.LadderExists( ladderid ):
					self.saybattle( self.socket,self.battleid, "Invalid ladderID." )
					return
				userlist, ranks = GlobalRankingAlgoSelector.GetCandidateOpponents( who, ladderid, self.db )
				opponent_found = False
				for user in userlist:
					try:
						userstatus = self.tsc.users[user]
					except: # skip offline
						continue
					if userstatus.ingame:
						continue
					if userstatus.afk:
						continue
					opponent_found = True
					self.saybattle( self.socket,self.battleid, ranks[user] )
				if not opponent_found:
					self.saybattle( self.socket,self.battleid, "No suitable candidates as opponent are available currently, try again later." )
		if command == "BATTLEOPENED" and len(args) > 12 and int(args[0]) == self.battleid:
			self.battlefounder = args[3]
			self.battleoptions["battletype"] = args[1]
			self.hostip = args[4]
			self.hostport = args[5]
			tabbedstring = " ".join(args[10:])
			tabsplit = parselist(tabbedstring,"\t")
			self.battleoptions["mapname"] = tabsplit[0]
			self.battleoptions["modname"] = tabsplit[2]
		if command == "UPDATEBATTLEINFO" and len(args) > 4 and int(args[0]) == self.battleid:
			tabbedstring = " ".join(args[4:])
			tabsplit = parselist(tabbedstring,"\t")
			self.battleoptions["mapname"] = tabsplit[0]

		if command == "CLIENTSTATUS" and len(args) > 1 and len(self.battlefounder) != 0 and args[0] == self.battlefounder:
			self.gamestarted = getingame(int(args[1]))
			self.JoinGame(s)
		if command == "CLIENTBATTLESTATUS":
			if len(args) != 3:
				error( "invalid CLIENTBATTLESTATUS:%s"%(args) )
			bs = BattleStatus( args[1], args[0] )
			self.battle_statusmap[ args[0] ] = bs
			self.FillTeamAndAllies()
		if command == "LEFTBATTLE":
			if len(args) != 2:
				error( "invalid LEFTBATTLE:%s"%(args) )
			if int(args[0]) == self.battleid:
				player = args[1]
				if player in self.battle_statusmap:
					del self.battle_statusmap[player]
					self.FillTeamAndAllies()
		if command == "ADDBOT":
			if len(args) != 6:
				error( "invalid ADDBOT:%s"%(args) )
			if int(args[0]) == self.battleid:
				botlib = args[5] # we'll use the bot's lib name intead of player name for ladder pourposes
				name = args[1]
				botlib = botlib.replace("|"," ")
				bs = BattleStatus( args[3], name )
				self.battle_statusmap[ name ] = bs
				self.FillTeamAndAllies()
				self.bots[name] = botlib
		if command == "UPDATEBOT":
			if len(args) < 2:
				error( "invalid UPDATEBOT:%s"%(args) )
			name = args[0]
			bs = BattleStatus( args[1], name )
			self.battle_statusmap[ botlib ] = bs
			self.FillTeamAndAllies()
		if command == "REMOVEBOT":
			if len(args) != 2:
				error( "invalid REMOVEBOT:%s"%(args) )
			if int(args[0]) == self.battleid:
				name = args[1]
				if name in self.bots:
					del self.bots[name]
				if name in self.battle_statusmap:
					del self.battle_statusmap[name]
				self.FillTeamAndAllies()

	def onloggedin(self,socket):
		sendstatus( self, socket )
		socket.send("JOINBATTLE " + str(self.battleid) + " " + self.battlepassword + "\n")

	def FillTeamAndAllies(self):
		self.teams = dict()
		self.allies = dict()
		for bs in self.battle_statusmap.values():
			if not bs.spec:
				if not bs.team in self.teams:
					self.teams[bs.team] = 1
				else:
					self.teams[bs.team] += 1
				if not bs.ally in self.allies:
					self.allies[bs.ally] = 1
				else:
					self.allies[bs.ally] += 1
#		print "allies:", self.allies
#		print "teams: ",self.teams
#		print "battle_statusmap",self.battle_statusmap

	def saybattle(self,socket,battleid,message):
		for line in message.split('\n'):
			self.log.Info( "Battle:%i, Message: %s" %(battleid,line) )
			socket.send("SAYBATTLE %s\n" % line)

	def saybattleex(self,socket,battleid,message):
		for line in message.split('\n'):
			self.log.Info( "Battle:%i, Message: %s" %(battleid,line) )
			socket.send("SAYBATTLEEX %s\n" % line)

	def sayPermissionDenied(self,socket, command, username ):
		socket.send("SAYPRIVATE %s You do not have sufficient access right to execute %s on this bot\n" %( username, command ) )

	def GetRankInfoDifference(self, pre, post ):
		#we cannot assume same ordering or even players in pre and post
		res = []
		for nick, info in post.iteritems():
			post_rank = info[0]
			post_pos = info[1]
			rank_type = info[2]
			if not nick in pre:
				pre_rank = rank_type()
				pre_pos = 0 #make num player on ladder +1
			else:
				pre_rank = pre[nick][0]
				pre_pos = pre[nick][1]
			res.append( '%s:\tNew position: %d (%d)\t New Rank: %s (was %s)'%(nick, post_pos, (pre_pos - post_pos),str(post_rank), str(pre_rank) ) )
		return res