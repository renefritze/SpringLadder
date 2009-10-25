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

if platform.system() == "Windows":
	import win32api
	
from utilities import *

def log(message):
	print green + message + normal
	
def saybattle( socket,battleid,message):
	print yellow+"Battle:%i, Message: %s" %(battleid,message) + normal
	socket.send("SAYBATTLE %s\n" % message)
		
def saybattleex(socket,battleid,message):
	print green+"Battle:%i, Message: %s" %(battleid,message) + normal
	socket.send("SAYBATTLEEX %s\n" % message)

bstr_nonneg = lambda n: n>0 and bstr_nonneg(n>>1)+str(n&1) or '0'

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
		sstr = bstr_nonneg( int(status) ).rjust( 31, "0" )
		print 'statusstring length:%d : [%s] from %s'%(len(sstr), sstr,status)
		self.team = int( sstr[-5:-2], 2)+1
		self.ally = int( sstr[-9:-6], 2)+1
		self.side = int( sstr[-27:-24], 2)+1
		self.spec = int ( sstr[-10], 2) == 1
		self.nick = nick

	def __str__(self):
		return "nick: %s -- team:%d ally:%d side:%d spec:%d"%(self.nick,self.team,self.ally,self.side,self.spec)

class Main:
	sock = 0
	battleowner = ""
	battleid = -1
	script = ""
	ingame = False
	gamestarted = False
	joinedbattle = False
	ladderid = -1
	scriptbasepath = os.environ['HOME']
	battleusers = dict()
	battleoptions = dict()
	ladderlist = dict()
	battle_statusmap = dict()
	teams = dict()
	allies = dict()
	battlefounder = ""
	def gs(self):# Game started
		self.gamestarted = 1
		
	def startspring(self,socket,g):
		cwd = os.getcwd()
		try:
			self.gamestarted = 0
			self.u.reset()
			if self.ingame == True:
				saybattle( self.socket, battleid, "Error: game is already running")
				return
			self.output = ""
			self.ingame = True
			if self.ladderid == -1 and self.db.LadderExists( ladderid ) and self.CheckValidSetup(self.ladderid,False,0):
				saybattleex(socket, battleid, "won't submit to the ladder the score results")
			else:
				saybattleex(socket, battleid, "is gonna submit to the ladder the score results")
			socket.send("MYSTATUS 1\n")
			st = time.time()
			if platform.system() == "Linux":
				log("*** Starting spring: command line \"%s\"" % (self.app.config["springdedpath"]+" "+os.path.join(os.environ['HOME'],"%f.txt" % g )))
				self.pr = subprocess.Popen((self.app.config["springdedpath"],os.path.join(os.environ['HOME'],"%f.txt" % g )),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
			else:
				log("*** Starting spring: command line \"%s\"" % (self.app.config["springdedpath"]+" "+os.path.join(os.environ['USERPROFILE'],"%f.txt" % g )))
				os.chdir("\\".join(self.app.config["springdedpath"].replace("/","\\").split("\\")[:self.app.config["springdedpath"].replace("/","\\").count("\\")]))
				self.pr = subprocess.Popen((self.app.config["springdedpath"],os.path.join(os.environ['USERPROFILE'],"%f.txt" % g )),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
			l = self.pr.stdout.readline()
			while len(l) > 0:
				self.output += l
				l = self.pr.stdout.readline()
			status = self.pr.wait()
			log("*** Spring has exited with status %i" % status )
			et = time.time()
			if status != 0:
				saybattle( self.socket,self.battleid,"Error: Spring Exited with status %i" % status)
				g = self.output.split("\n")
				for h in g:
					log("*** STDOUT+STDERR: "+h)
					time.sleep(float(len(h))/900.0+0.05)
			socket.send("MYSTATUS 0\n")
			if True:
				saybattle("has submitted ladder score updates")
		except:
			exc = traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],sys.exc_info()[2])
			loge(socket,"*** EXCEPTION: BEGIN")
			for line in exc:
				loge(socket,line)
			loge(socket,"*** EXCEPTION: END")
			os.chdir(cwd)
		os.chdir(cwd)
		self.ingame = False
		
	def KillBot(self):
		if platform.system() == "Windows":
			handle = win32api.OpenProcess(1, 0, os.getpid())
			win32api.TerminateProcess(handle, 0)
		else:
			os.kill(os.getpid(),signal.SIGKILL)
			
	def CheckValidSetup( self, ladderid, echoerrors, socket ):
		return self.CheckvalidPlayerSetup(ladderid,echoerrors,socket) and self.CheckValidOptionsSetup(ladderid,echoerrors,socket)
		
	def CheckvalidPlayerSetup( self, ladderid, echoerrors, socket ):
		IsOk = True
		laddername = self.db.GetLadderName( ladderid )
		teamcount = len(self.teams)
		allycount = len(self.allies)
		if teamcount < self.db.GetLadderOption( ladderid, "min_team_count" ):
			if echoerrors:
				saybattle( socket, self.battleid, "There are too few control teams for" + laddername  + " (" + str(teamcount) + ")" )
			IsOk =  False
		if teamcount > self.db.GetLadderOption( ladderid, "max_team_count" ):
			if echoerrors:
				saybattle( socket, self.battleid, "There are too many control teams for" + laddername + " (" + str(teamcount) + ")" )
			IsOk = False
		if allycount < self.db.GetLadderOption( ladderid, "min_ally_count" ):
			if echoerrors:
				saybattle( socket, self.battleid, "There are too few allies for" + laddername  + " (" + str(teamcount) + ")" )
			IsOk = False
		if allycount > self.db.GetLadderOption( ladderid, "max_ally_count" ):
			if echoerrors:
				saybattle( socket, self.battleid, "There are too few allies for" + laddername  + " (" + str(teamcount) + ")" )
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
		return IsOK
			
	def CheckOptionOk( self, ladderid, keyname, value ):
		if self.db.GetOptionKeyValueExists( self.ladderid, False, keyname, value ): # option in the blacklist
			return False
		if self.db.GetOptionKeyExists( self.ladderid, True, keyname ): # whitelist not empty
			return self.db.GetOptionKeyValueExists( self.ladderid, True, keyname, value )
		else:
			return True
			
	def onload(self,tasc):
		self.app = tasc.main
		self.hosttime = time.time()
		self.battleid = int(self.app.config["battleid"])
		self.ladderid = int(self.app.config["ladderid"])
		self.db = LadderDB( parselist(self.app.config["alchemy-uri"],",")[0], parselist(self.app.config["alchemy-verbose"],",")[0] )
		
	def oncommandfromserver(self,command,args,s):
		#print "From server: %s | Args : %s" % (command,str(args))
		self.socket = s
		if command == "JOINBATTLE":
			self.joinedbattle = True
			log( "joined battle: " + str(self.battleid) )
			self.socket.send( "MYBATTLESTATUS 512 255\n" )#spectator/white 
		if command == "JOINBATTLEFAILED":
			self.joinedbattle = False
			error( "Join battle failed, ID: " + str(self.battleid) + " reason: " + " ".join(args[0:] ) )
			self.KillBot()
		if command == "FORCEQUITBATTLE":
			self.joinedbattle = False
			log( "kicked from battle: " + str(self.battleid) )
			self.KillBot()
		if command == "BATTLECLOSED" and len(args) == 1 and int(args[0]) == self.battleid:
			self.joinedbattle = False
			log( "battle closed: " + str(self.battleid) )
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
			self.socket.send("MYBATTLESTATUS \n")
		if command == "SAIDBATTLE" and len(args) > 1 and args[1].startswith("!"):
			who = args[0]
			command = args[1]
			args = args[2:]
			print command
			print args
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
			if command == "!ladder":
				if len(args) == 1 and args[0].isdigit():
					ladderid = int(args[0])
					if ladderid != -1:
						if self.db.LadderExists( ladderid ):
							saybattle( self.socket, self.battleid,"Enabled ladder reporting for ladder: " + self.db.GetLadderName( ladderid ) )
							self.ladderid = ladderid
							if self.CheckValidSetup( ladderid, True, self.sockets ):
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
				log( "leaving battle: " + str(self.battleid) )
				self.socket.send("LEAVEBATTLE\n")
				self.KillBot()
		if command == "BATTLEOPENED" and len(args) > 12 and int(args[0]) == self.battleid:
			self.battlefounder == args[3]
			self.battleoptions["battletype"] = args[1]
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
				print"*** EXCEPTION: END"+normale
			if self.joinedbattle: #start spring
				s.send("MYSTATUS 1\n")
				g = time.time()
				try:
					os.remove(os.path.join(self.scriptbasepath,"%f.txt" % g))
				except:
					pass
				if platform.system() == "Linux":
					f = open(os.path.join(os.environ['HOME'],"%f.txt" % g),"a")
				else:
					f = open(os.path.join(os.environ['USERPROFILE'],"%f.txt" % g),"a")
				self.script = ""
				f.write(self.script)
				f.close()
				thread.start_new_thread(self.startspring,(s,g))
		if command == "CLIENTBATTLESTATUS":
			if len(args) != 3:
				error( "invalid CLIENTBATTLESTATUS:%s"%(args) )
			bs = BattleStatus( args[1], args[0] )
			self.battle_statusmap[ args[0] ] = bs
			print bs
			self.FillTeamAndAllies()
		
	def onloggedin(self,socket):
		if self.ingame == True:
			socket.send("MYSTATUS 1\n")
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
		print self.allies
		print self.teams
