# -*- coding: utf-8 -*-
from colors import *
from ParseConfig import *
import commands
import thread
import signal
import os
import time
import udpinterface
import subprocess
import traceback
import platform
import sys

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
	ingame = 0
	gamestarted = 0
	ladderid = -1
	scriptbasepath = os.environ['HOME']
	battleusers = dict()
	battleoptions = dict()
	ladderlist = dict()
	mapname = ""
	
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
			if self.ladderid == -1 and self.checkvalidsetup():
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
		
	def killbot(self):
		if platform.system() == "Windows":
			handle = win32api.OpenProcess(1, 0, os.getpid())
			win32api.TerminateProcess(handle, 0)
		else:
			os.kill(os.getpid(),signal.SIGKILL)
			
	def checkvalidsetup(self):
		return self.checkvalidplayersetup() and self.checkvalidoptionssetup() and self.checkgeneraloptionssetup()
		
	def checkvalidplayersetup(self):
		if self.ladderid == -1:
			return True
			
	def checkvalidoptionssetup(self):
		if self.ladderid == -1:
			return True
			
	def checkgeneraloptionssetup(self):
		if self.ladderid == -1:
			return True
			
	def onload(self,tasc):
		self.app = tasc.main
		self.hosttime = time.time()
		self.battleid = int(self.app.config["battleid"])
		self.ladderid = int(self.app.config["ladderid"])
		
	def oncommandfromserver(self,command,args,s):
		#print "From server: %s | Args : %s" % (command,str(args))
		self.sock = s
		if command == "JOINBATTLE":
			pass
		if command == "JOINBATTLEFAILED":
			error( "Join battle failed, ID: " + str(self.battleid) + " reason: " + " ".join(args[0:] )
			self.killbot()
		if command == "SETSCRIPTTAGS":
			for option in args:
				pieces = parselist( option, "=" )
				if len(pieces) != 2:
					error( "parsing error of option string: " + option )
				key = pieces[0]
				value = pieces[1]
				self.battleoptions[key] = value
			self.checkvalidoptionssetup()
		if command == "REQUESTBATTLESTATUS":
			socket.send("MYBATTLESTATUS \n")
		if command == "SAIDBATTLE" and len(args) > 1 and args[1].startswith("!"):
			who = args[0]
			command = args[1]
			args = args[2:]
			if command == "!ladder" and len(args) == 1:
				if args[0].isdigit():
					ladderid = int(args[0])
					if ladderid == -1:
						self.ladderid = ladderid
						saybattle(socket, self.battleid, "ladder mode disabled")
					elif ladderid in self.ladderlist:
						self.ladderid = ladderid
						saybattle(socket, self.battleid, "ladder set to " + self.ladderlist[ladderid])
					else:
						saybattle(socket, self.battleid, "invalid ladder ID, use !ladderlist for a list of valid ID")
				else:
					saybattle(socket, self.battleid, "malformed message, it's !ladder ladderID, use -1 as ladderID to disable")
			if command == "!ladderlist":
				for i in self.ladderlist:
					saybattle( socket, self.battleid, self.ladderlist[i] + ": " + str(i) )
			if command == "!ladderlistoptions":
				if len(args) > 1:
					saybattle(socket, self.battleid, "Invalid command syntax, check !help for usage." )
				else:
					ladderid = self.ladderid
					if len(args)
						ladderid = int(args[0])
					if ( ladderid in self.ladderlist ):
						whitelist = self.ladderoptions[ladderid].allowedoptions
						blacklist = self.ladderoptions[ladderid].restrictedoptions
						saybattle(socket, self.battleid, "Ladder: " + self.ladderlist[ladderid] )
						saybattle(socket, self.battleid, "modname: " + self.ladderoptions[ladderid].modname )
						saybattle(socket, self.battleid, "Min control team size: " + str(self.ladderoptions[ladderid].controlteamminsize) )
						saybattle(socket, self.battleid, "Max control team size: " + str(self.ladderoptions[ladderid].controlteammaxsize) )
						saybattle(socket, self.battleid, "Min ally size: " + str(self.ladderoptions[ladderid].allyminsize) )
						saybattle(socket, self.battleid, "Max ally size: " + str(self.ladderoptions[ladderid].allymaxsize) )
						saybattle(socket, self.battleid, "Whitelisted options ( if a key is present, no other value except for those listed will be allowed for such key ):" )
						for key in whitelist:
							allowedvalues = whitelist[key]
							for value in allowedvalues:
								saybattle(socket, self.battleid, key + ": " + value )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Blacklisted options ( if a value is present for a key, such value won't be allowed ):" )
						for key in blacklist:
							disabledvalues = blacklist[key]
							for value in disabledvalues:
								saybattle(socket, self.battleid, key + ": " + value )						
					else:
						saybattle(socket, self.battleid, "Invalid ladder ID, use !ladderlist for a list of valid ID." )
		if command == "BATTLEOPENED" and len(args) > 12 and int(args[0]) == self.battleid:
			if args[1] != 0: # battle is not the right type
				error( "Battle is not the right type, ID: " + str(self.battleid) + " type: " + args[1] )
				self.killbot()
			self.mapname = args[10]
			self.modname = args[12]
		if command == "UPDATEBATTLEINFO" and len(args) > 4 and int(args[0]) == self.battleid:
			self.mapname = args[4]
			self.checkgeneraloptionssetup()
		
				if args[1] == "!startgame" and args[0] == self.battleowner:
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
		self.hosted = 0	
		if self.ingame == 1:
			socket.send("MYSTATUS 1\n")
		socket.send("JOINBATTLE " + self.battleid + "\n")
