# -*- coding: utf-8 -*-
from colors import *
from ParseConfig import *
import commands
import thread
import signal
import os
import time
import subprocess
import traceback
import platform
import sys
from db_entities import *
from ladderdb import *
from colors import *
from match import *
from ranking import GlobalRankingAlgoSelector
if platform.system() == "Windows":
	import win32api

from utilities import *

def log(message):
	print green + message + normal

def saybattle( socket,battleid,message):
	for line in message.split('\n'):
		print yellow+"Battle:%i, Message: %s" %(battleid,line) + normal
		socket.send("SAYBATTLE %s\n" % line)

def saybattleex(socket,battleid,message):
	for line in message.split('\n'):
		print green+"Battle:%i, Message: %s" %(battleid,line) + normal
		socket.send("SAYBATTLEEX %s\n" % line)

def sayPermissionDenied(socket, command, username ):
	socket.send("SAYPRIVATE %s You do not have sufficient access right to execute %s on this bot\n" %( username, command ) )

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
#		print "len before padding: ",len(bstr_nonneg( int(status) ))
		sstr = bstr_nonneg( int(status) ).rjust( 31, "0" )
#s		print 'statusstring length:%d : [%s] from %s'%(len(sstr), sstr,status)
		self.team = int( sstr[-6:-2], 2)+1
		self.ally = int( sstr[-10:-6], 2)+1
		self.side = int( sstr[-28:-24], 2)+1
		self.spec = ( sstr[ -11:-10 ] == "0" )
		self.nick = nick
		self.decimal = int(status)

	def __str__(self):
		return "nick: %s -- team:%d ally:%d side:%d spec:%d decimal:%d"%(self.nick,self.team,self.ally,self.side,self.spec,self.decimal)

helpstring_user = """!ladderlist : lists available ladders with their IDs
!ladder ladderID: sets the ladder to report scores to, -1 to disable reporting
!ladderlistoptions ladderID : lists enforced options for given ladderID
!checksetup : checks that all options and player setup are compatible with current set ladder
!checksetup ladderID: checks that all options and player setup are compatible for given ladderID
"""

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
	battlefounder = ""
	hostip = ""
	hostport = 0
	def startspring(self,socket,g):
		currentworkingdir = os.getcwd()
		try:
			if self.ingame == True:
				saybattle( self.socket, self.battleid, "Error: game is already running")
				return
			self.output = ""
			self.ingame = True
			doSubmit = self.ladderid != -1 and self.db.LadderExists( self.ladderid ) and self.CheckValidSetup(self.ladderid,False,0)
			if doSubmit:
				saybattleex(socket, self.battleid, "is gonna submit to the ladder the score results")
			else:
				saybattleex(socket, self.battleid, "won't submit to the ladder the score results")
			sendstatus( self, socket )
			st = time.time()
			log("*** Starting spring: command line \"%s %s\"" % (self.app.config["springdedclientpath"], os.path.join(self.scriptbasepath,"%f.txt" % g )) )
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
				saybattle( self.socket,self.battleid,"Error: Spring Exited with status %i" % status)
				g = self.output.split("\n")
				for h in g:
					print yellow + "*** STDOUT+STDERR: " + h + normal
					time.sleep(float(len(h))/900.0+0.05)
			elif doSubmit:
				mr = MatchToDbWrapper( self.output, battlefounder, self.ladderid )
				try:
					self.db.ReportMatch( mr )
					saybattleex(socket, self.battleid, "has submitted ladder score updates")
				except:
					saybattle( self.socket,self.battleid,"There was an error reporting the battle outcome." )
			else:
				log("*** Spring has exited with status %i" % status )
			sendstatus( self, socket )

		except:
			exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
			print red+"*** EXCEPTION: BEGIN"
			for line in exc:
				print line
			print "*** EXCEPTION: END"+normal
			os.chdir(currentworkingdir)
			self.ingame = False
		os.chdir(currentworkingdir)
		self.ingame = False

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
			saybattle( socket, self.battleid, "There are banned player for " + laddername  + " (" + bannedplayers + " )" )
		if not len(duplicatebots) == 0 and echoerrors:
			saybattle( socket, self.battleid, "There are too many bots of the same type (" + duplicatebots + " )" )

		minbotcount = self.db.GetLadderOption( ladderid, "min_ai_count" )
		maxbotcount = self.db.GetLadderOption( ladderid, "max_ai_count" )
		minteamcount = self.db.GetLadderOption( ladderid, "min_team_count" )
		maxteamcount = self.db.GetLadderOption( ladderid, "max_team_count" )
		minallycount = self.db.GetLadderOption( ladderid, "min_ally_count" )
		maxallycount = self.db.GetLadderOption( ladderid, "max_ally_count" )
		if botcount < minbotcount:
			if echoerrors:
				saybattle( socket, self.battleid, "There are too few AIs for " + laddername  + " (" + str(botcount) + ")" )
			IsOk =  False
		if botcount > maxbotcount:
			if echoerrors:
				saybattle( socket, self.battleid, "There are too many AIs for " + laddername + " (" + str(botcount) + ")" )
			IsOk = False
		if teamcount < minteamcount:
			if echoerrors:
				saybattle( socket, self.battleid, "There are too few control teams for " + laddername  + " (" + str(teamcount) + ")" )
			IsOk =  False
		if teamcount > maxteamcount:
			if echoerrors:
				saybattle( socket, self.battleid, "There are too many control teams for " + laddername + " (" + str(teamcount) + ")" )
			IsOk = False
		if allycount < minallycount:
			if echoerrors:
				saybattle( socket, self.battleid, "There are too few allies for " + laddername  + " (" + str(allycount) + ")" )
			IsOk = False
		if allycount > maxallycount:
			if echoerrors:
				saybattle( socket, self.battleid, "There are too few allies for " + laddername  + " (" + str(allycount) + ")" )
			IsOk = False
		minteamsize = self.db.GetLadderOption( ladderid, "min_team_size" )
		maxteamsize = self.db.GetLadderOption( ladderid, "max_team_size" )
		minallysize = self.db.GetLadderOption( ladderid, "min_ally_size" )
		maxallysize = self.db.GetLadderOption( ladderid, "max_team_size" )
		teamsizesok = True
		errorstring = "The following control teams have too few players in them for " + laddername + ":\n"
		for team in self.teams:
			teamsize = self.teams[team]
			if teamsize < minteamsize:
				errorstring += str(team) + "=" + str(teamsize) + " "
				teamsizesok = False
				IsOk = False
		if not teamsizesok and echoerrors:
			saybattle( socket, self.battleid, errorstring )
		teamsizesok = True
		errorstring = "The following control teams have too many players in them for " + laddername + ":\n"
		for team in self.teams:
			if teamsize > maxteamsize:
				IsOk = False
				errorstring += str(team) + "=" + str(teamsize) + " "
				teamsizesok = False
		if not teamsizesok and echoerrors:
			saybattle( socket, self.battleid, errorstring )
		allysizesok = True
		errorstring = "The following ally have too few players in them for " + laddername + ":\n"
		for ally in self.allies:
			allysize = self.allies[ally]
			if allysize < minallysize:
				IsOk = False
				allysizesok = False
				errorstring += str(team) + "=" + str(teamsize) + " "
		if not allysizesok and echoerrors:
			saybattle( socket, self.battleid, errorstring )
		allysizesok = True
		errorstring = "The following ally have too many players in them for " + laddername + ":\n"
		for ally in self.allies:
			allysize = self.allies[ally]
			if allysize > maxallysize:
				IsOk = False
				allysizesok = False
				errorstring += str(team) + "=" + str(teamsize) + " "
		if not allysizesok and echoerrors:
			saybattle( socket, self.battleid, errorstring )
		return IsOk


	def CheckValidOptionsSetup( self, ladderid, echoerrors, socket ):
		IsOk = True
		laddername = self.db.GetLadderName( ladderid )
		for key in self.battleoptions:
			value = self.battleoptions[key]
			OptionOk = self.CheckOptionOk( ladderid, key, value )
			if not OptionOk:
				if IsOk and echoerrors:
					saybattle( socket, self.battleid, "The following settings are not compatible with " + laddername + ":" )
				IsOk = False
				if echoerrors:
					saybattle( socket, self.battleid, key + "=" + value )
		return IsOk

	def CheckOptionOk( self, ladderid, keyname, value ):
		if self.db.GetOptionKeyValueExists( ladderid, False, keyname, value ): # option in the blacklist
			return False
		if self.db.GetOptionKeyExists( ladderid, True, keyname ): # whitelist not empty
			return self.db.GetOptionKeyValueExists( ladderid, True, keyname, value )
		else:
			return True

	def onload(self,tasc):
		self.app = tasc.main
		self.tsc = tasc
		self.hosttime = time.time()
		self.battleid = int(self.app.config["battleid"])
		self.ladderid = int(self.app.config["ladderid"])
		self.db = LadderDB( parselist(self.app.config["alchemy-uri"],",")[0], parselist(self.app.config["alchemy-verbose"],",")[0] )

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
			self.KillBot()
		if command == "BATTLECLOSED" and len(args) == 1 and int(args[0]) == self.battleid:
			self.joinedbattle = False
			notice( "Battle closed: " + str(self.battleid) )
			self.KillBot()
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
				value = pieces[1]
				self.battleoptions[key] = value
		if command == "REQUESTBATTLESTATUS":
			self.socket.send( "MYBATTLESTATUS 4194816 255\n" )#spectator+synced/white
		if command == "SAIDBATTLE" and len(args) > 1 and args[1].startswith("!"):
			who = args[0]
			command = args[1]
			args = args[2:]

			if len(command) > 0 and command[0] == "!" and ( who == self.battlefounder or who == self.app.config["fromwho"] ) :
				if not self.db.AccessCheck( -1, who, Roles.User ):
					sayPermissionDenied( socket, who, command )
					#log
					return
			else:
				return

			if command == "!ladderchecksetup":
				ladderid = self.ladderid
				if len(args) == 1 and args[0].isdigit():
					ladderid = int(args[0])
				if ladderid == -1:
					saybattle( self.socket, self.battleid,"No ladder has been enabled.")
				elif self.db.LadderExists( ladderid ):
					laddername = self.db.GetLadderName( ladderid )
					if self.CheckValidSetup( ladderid, True, self.socket ):
						saybattle( self.socket, self.battleid, "All settings are compatible with the ladder " + laddername )
				else:
					saybattle( self.socket, self.battleid,"Invalid ladder ID.")
			if command == "!ladderlist":
				saybattle( self.socket, self.battleid, "Available ladders, format name: ID:" )
				for l in self.db.GetLadderList(Ladder.name):
					saybattle( self.socket, self.battleid, "%s: %d" %(l.name, l.id ) )
			if command == "!ladder":
				if len(args) == 1 and args[0].isdigit():
					ladderid = int(args[0])
					if ladderid != -1:
						if self.db.LadderExists( ladderid ):
							laddername = self.db.GetLadderName( ladderid )
							saybattle( self.socket, self.battleid,"Enabled ladder reporting for ladder: " + laddername )
							self.ladderid = ladderid
							if self.CheckValidSetup( ladderid, True, self.socket ):
								saybattle( self.socket, self.battleid, "All settings are compatible with the ladder " + laddername )
						else:
							saybattle( self.socket, self.battleid,"Invalid ladder ID.")
					else:
						self.ladderid = ladderid
						saybattle( self.socket, self.battleid,"Ladder reporting disabled.")
				else:
					saybattle( self.socket, self.battleid,"Invalid command syntax, check !help for usage.")
			if command == "!ladderleave":
				self.joinedbattle = False
				good( "Leaving battle: " + str(self.battleid) )
				self.socket.send("LEAVEBATTLE\n")
				self.KillBot()
			if command == "!help":
				saybattle( self.socket, self.battleid,  "Hello, I am a bot to manage and keep stats of ladder games.\nYou can use the following commands:")
				saybattle( self.socket, self.battleid, helpstring_user )
			if command == '!debug':
				if not self.db.AccessCheck( self.ladderid, who, Roles.GlobalAdmin ):
					sayPermissionDenied( self.socket, who, command )
					#log
					return
				import fakeoutput
				if len(args) > 0 and args[0].isdigit():
					idx = max( int(args[0]), len(fakeoutput.fakeoutput) -1 )
					output = fakeoutput.fakeoutput[idx]
				else:
					output = fakeoutput.fakeoutput[-1]
				
				upd = GlobalRankingAlgoSelector.GetPrintableRepresentation( self.db.GetRanks( self.ladderid ), self.db )
				saybattle( self.socket, self.battleid, 'output used:\n' + output + 'produced:\n' )
				saybattle( self.socket, self.battleid, 'before:\n' + upd )
				try:
					mr = MatchToDbWrapper( output, self.ladderid )
					for i in range(2):
						self.db.ReportMatch( mr, False )#false skips validation check of output against ladder rules
					upd = GlobalRankingAlgoSelector.GetPrintableRepresentation( self.db.GetRanks( self.ladderid ), self.db )
					saybattle( self.socket, self.battleid, 'pre-recalc:\n' +upd )
					self.db.RecalcRankings(self.ladderid)
				except InvalidOptionSetup, e:
					saybattle( self.socket, self.battleid, str(e) )
					return

				upd = GlobalRankingAlgoSelector.GetPrintableRepresentation( self.db.GetRanks( self.ladderid ), self.db )
				saybattle( self.socket, self.battleid, 'after:\n' +upd )
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
		if command == "CLIENTSTATUS" and len(args) > 0 and len(self.battlefounder) != 0 and args[0] == self.battlefounder:
			try:
				self.gamestarted = self.tsc.users[self.battlefounder].ingame
			except:
				exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
				print red+"*** EXCEPTION: BEGIN"
				for line in exc:
					print line
				print"*** EXCEPTION: END"+normal
			if self.joinedbattle: #start spring
				sendstatus( self, self.socket )
				g = time.time()
				try:
					os.remove(os.path.join(self.scriptbasepath,"%f.txt" % g))
				except:
					pass
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
		socket.send("JOINBATTLE " + str(self.battleid) + "\n")

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
