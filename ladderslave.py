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

if platform.system() == "Windows":
	import win32api
	
from utilities import *

def log(message):
	print green + message + normal
	
def saybattle(socket,battleid,message):
	try:
		print orange+"Battle:%i, Message: %s" %(battleid,message) + normal
		s.send("SAYBATTLE %s\n" % message)
	except:
		pass
		
def saybattleex(socket,battleid,message):
	try:
		print pink+"Battle:%i, Message: %s" %(battleid,message) + normal
		s.send("SAYBATTLEEX %s\n" % message)
	except:
		pass
	 	
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
	battlefounder = ""
	def gs(self):# Game started
		self.gamestarted = 1
		
	def startspring(self,socket,g):
		cwd = os.getcwd()
		try:
			self.gamestarted = 0
			self.u.reset()
			if self.ingame == 1:
				saybattle(socket, battleid, "Error: game is already running")
				return
			self.output = ""
			self.ingame = 1
			if self.ladderid == -1 and self.CheckValidSetup(self.ladderid,False):
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
				saybattle(socket,self.battleid,"Error: Spring Exited with status %i" % status)
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
		self.ingame = 0
		self.gamestarted = 0
		
	def KillBot(self):
		if platform.system() == "Windows":
			handle = win32api.OpenProcess(1, 0, os.getpid())
			win32api.TerminateProcess(handle, 0)
		else:
			os.kill(os.getpid(),signal.SIGKILL)
			
	def CheckValidSetup( self, ladderid, echofailures ):
		if self.ladderid == -1:
			if echofailures:
				self.socket.saybattle(self.battleid,"No ladder has been chosen.")
			return False
		else:
			return self.CheckvalidPlayerSetup(ladderid,echofailures) and self.CheckValidOptionsSetup(ladderid,echofailures)
		
	def CheckvalidPlayerSetup( self,ladderid , echofailures ):
		if self.ladderid == -1:
			if echofailures:
				self.socket.saybattle(self.battleid,"No ladder has been chosen.")
			return False
			
	def CheckValidOptionsSetup( self, ladderid, echofailures ):
		if self.ladderid == -1:
			if echofailures:
				self.socket.saybattle(self.battleid,"No ladder has been chosen.")
			return False
		IsOk = True
		for key in self.battleoptions:
			valud = self.battleoption[key]
			OptionOk = self.CheckOptionOk( ladderid, key, value )
			if not OptionOk:
				IsOk = False
				self.socket.saybattle(self.battleid,"Incompatible battle option detected: " + key + "=" + value )
			
	def CheckOptionOk( self, ladderid, keyname, value ):
		if self.db.GetOptionKeyValueExists( self.ladderid, False, key, value ): # option in the blacklist
			return False
		if self.db.GetOptionKeyExists( self.ladderid, True, keyname ): # whitelist not empty
			return self.db.GetOptionKeyValueExists( self.ladderid, True, key, value )
		else:
			return True
			
	def onload(self,tasc):
		self.app = tasc.main
		self.hosttime = time.time()
		self.battleid = int(self.app.config["battleid"])
		self.ladderid = int(self.app.config["ladderid"])
		self.db = LadderDB( parselist(self.app.config["alchemy-uri"],",")[0] )
		
	def oncommandfromserver(self,command,args,s):
		#print "From server: %s | Args : %s" % (command,str(args))
		self.sock = s
		if command == "JOINBATTLE":
			self.joinedbattle = True
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
			for option in args:
				pieces = parselist( option, "=" )
				if len(pieces) != 2:
					error( "parsing error of option string: " + option )
				key = pieces[0]
				if key.startswith("/game/"): # strip prefix
					key = key[5:]
				elif key.startswith("game/"):#  strip prefix
					key = key[4:]
				value = pieces[1]
				self.battleoptions[key] = value
		if command == "REQUESTBATTLESTATUS":
			socket.send("MYBATTLESTATUS \n")
		if command == "SAIDBATTLE" and len(args) > 1 and args[1].startswith("!"):
			who = args[0]
			command = args[1]
			args = args[2:]
			if command == "!ladderchecksetup":
				ladderid = self.ladderid
				if len(args) == 1 and args[0].isdigit():
					ladderid = int(args[0])
				self.CheckValidSetup( ladderid, True )
			if command == "!ladder":
				if len(args) == 1 and args[0].isdigit():
					ladderid = int(args[0])
					if ladderid != -1:
						if self.db.LadderExists( ladderid ):
							self.socket.saybattle(self.battleid,"Enabled ladder reporting for ladder: " + self.db.GetLadderName( ladderid ) )
							self.ladderid = ladderid
							self.CheckValidSetup( ladderid, True )
						else:
							self.socket.saybattle(self.battleid,"Invalid ladder ID.")
					else:
						self.ladderid = ladderid
						self.socket.saybattle(self.battleid,"Ladder reporting disabled.")
				else:
					self.socket.saybattle(self.battleid,"Invalid command syntax, check !help for usage.")
			if command == "!ladderleave":
				self.joinedbattle = False
				log( "leaving battle: " + str(self.battleid) )
				socket.send("LEAVEBATTLE\n")
				self.KillBot()
		if command == "BATTLEOPENED" and len(args) > 12 and int(args[0]) == self.battleid:
			self.battlefounder == args[3]
			self.battleoptions["battletype"] = args[1]
			self.battleoptions["mapname"] = args[10]
			self.battleoptions["modname"] = args[12]
		if command == "UPDATEBATTLEINFO" and len(args) > 4 and int(args[0]) == self.battleid:
			self.battleoptions["mapname"] = args[4]
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
			
	def onloggedin(self,socket):
		if self.ingame == True:
			socket.send("MYSTATUS 1\n")
		socket.send("JOINBATTLE " + str(self.battleid) + "\n")
