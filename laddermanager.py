# -*- coding: utf-8 -*-
from colors import *
from ParseConfig import *
import commands
import thread
import os
import sys
import signal
import traceback
import subprocess
from db_entities import *
from ladderdb import *

helpstring_admin = """!ladderadd laddername : creates a new ladder
!ladderremove ladderID : deletes a ladder
!ladderchangecontrolteamsize ladderID value : sets the control team size (player ID) used by the ladder
!ladderchangecontrolteamsize ladderID min max : sets the control team size (player ID) used by the ladder
!ladderchangeallysize ladderID value : sets the ally team size used by the ladder
!ladderchangeallysize ladderID min max : sets the ally team size used by the ladder
!ladderaddoption ladderID blacklist/whitelist optionkey optionvalue : adds a new rule to the ladder, blacklist/whitelist is boolean and 1 means whitelist, a given key cannot have a whitelist and blacklist at the same time
!ladderremoveoption ladderID optionkey optionvalue : removes optionvalue from the ladder rules, if the optionkey has no values anymore it will be automatically removed
!laddercopy source_id target_name : copy ladder with source_id to new ladder named target_name including all options"""


helpstring_user = """!ladderlist : lists available ladders with their IDs
!ladder : requests a bot to join your current game to monitor and submit scores
!ladder ladderID: requests a bot to join your current game to monitor and submit scores got given ladderID
!ladderlistoptions ladderID : lists enforced options for given ladderID
!score ladderID : lists scores for all the players for the given ladderID
!score playername : lists scores for the given player in all ladders
!score ladderID playername : lists score for the given player for the given ladderID"""

def pm(s,p,m):
	try:
		for line in m.split('\n'):
			print yellow+"PM To:%s, Message: %s" %(p,line) + normal
			s.send("SAYPRIVATE %s %s\n" %(p,line))
	except:
		pass
		
def saychannel( socket, channel, message ):
		for line in message.split('\n'):
			print purple+"Channel :%s, Message: %s" %(channel,line) + normal
			socket.send("SAY %s %s\n" %(channel,line) )
			
class Main:
	botpid = dict() # slot -> bot pid
	botstatus = dict() # slot -> bot already spawned
	battleswithbots = dict() # battle id -> bot already in
	ladderlist = dict() # id -> ladder name
	ladderoptions = dict() # id -> ladder options
	
	def botthread(self,slot,battleid,ladderid,ist):
		nick = self.app.config["nick"]+str(slot)
		try:
			d = dict()
			d.update([("serveraddr",self.app.config["serveraddr"])])
			d.update([("serverport",self.app.config["serverport"])])
			d.update([("admins",self.app.config["admins"])])
			d.update([("nick",nick)])
			d.update([("password",self.app.config["password"])])
			d.update([("plugins","ladderslave")])
			d.update([("bans",self.app.config["bans"])])
			d.update([("battleid",str(battleid))])
			d.update([("ladderid",str(ladderid))])
			d.update([("alchemy-uri",self.app.config["alchemy-uri"])])
			writeconfigfile(nick+".cfg",d)
			p = subprocess.Popen(("python","Main.py","-c", "%s" % (nick+".cfg")),stdout=sys.stdout)
			self.botpid[slot] = p.pid
			p.wait()
			self.ul.remove(r)
		except:
			print '-'*60
			traceback.print_exc(file=sys.stdout)
			print '-'*60
			
	def onload(self,tasc):
		self.tsc = tasc
		self.bans = []
		self.app = tasc.main
		self.channels = parselist(self.app.config["channelautojoinlist"],",")
		self.admins = parselist(self.app.config["admins"],",")
		self.db = LadderDB( parselist(self.app.config["alchemy-uri"],",")[0] )
		
	def notifyuser( self, socket, fromwho, fromwhere, ispm, message ):
		if fromwhere == "main":
			ispm = true
		if not ispm:
			saychannel( socket, fromwhere, message )
		else:
			pm( socket, fromwho, message )
			
	def spawnbot( self,  socket, battleid, ladderid ):	
		slot = len(self.botstatus)
		self.threads.append(thread.start_new_thread(self.botthread,(slot,socket,battleid,ladderid)))
		self.botstatus[slot] = True
		
	def oncommandfromuser(self,fromwho,fromwhere,ispm,command,args,socket):
		if fromwho == self.app.config["nick"]:
			return
		if command == "!ladder":
			if len(args) > 1:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax or command not found, use !help for a list of available commands and their usage." )
			else:
				ladderid = -1
				battleid = -2
				if len(args) == 1 and args[0].isdigit():
					ladderid = int(args[0])
				try:
					battleid = self.tsc.users[fromwho].battleid
				except:
					bad("User " + fromwho + " not found")
				if ( battleid < 0 ):
					self.notifyuser( socket, fromwho, fromwhere, ispm, "You are not in a battle." )
				else:
					if ( battleid in self.battleswithbots ):
						self.notifyuser( socket, fromwho, fromwhere, ispm, "A ladder bot is already present in your battle." )
					else:
						if ( ladderid == -1 or self.db.LadderExists( ladderid ) ):
							self.spawnbot( socket, battleid, ladderid )
						else:
							self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderjoinchannel":
			if fromwho in self.admins:
				if len(args) < 1:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					channel = " ".join(args[0:])
					socket.send("JOIN " + channel + "\n")
					if not channel in self.channels:
						self.channels.append(channel)
						self.app.config["channelautojoinlist"] = ','.join(self.channels)
						self.app.SaveConfig()
		if command == "!ladderleavechannel":
			if fromwho in self.admins:
				if len(args) != 1:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					channel = args[0]
					if channel in self.channels:
						socket.send("LEAVE " + channel + "\n")
						self.channels.remove(channel)
						self.app.config["channelautojoinlist"] = ','.join(self.channels)
						self.app.SaveConfig()		
		if command == "!ladderlist":
			self.notifyuser( socket, fromwho, fromwhere, ispm, "Available ladders, format name: ID:" )
			for l in self.db.GetLadderList(Ladder.name):
				self.notifyuser( socket, fromwho, fromwhere, ispm, "%s: %d" %(l.name, l.id ) )
		if command == "!ladderadd":
			if ( fromwho in self.admins ):
				if len(args) < 1:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder name can't be empty." )
				else:
					try:
						laddername = " ".join(args[0:])
						ladderid = self.db.AddLadder( laddername )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "New ladder created, ID: " + str(ladderid) ) 
					except ElementExistsException, e:
						print "Error",e
		if command == "!ladderremove":
			if ( fromwho in self.admins ):
				if len(args) != 1 or not args[0].isdigit():
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					ladderid = int(args[0])
					try:
						self.db.RemoveLadder( args[0] )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder removed." )
					except ElementNotFoundException, e:
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderchangecontrolteamsize":
			if fromwho in self.admins:
				if len(args) > 3 or not args[0].isdigit() or not args[1].isdigit():
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					ladderid = int(args[0])
					if ( ladderid in self.ladderlist ):
						if len(args) == 2: # min = max
							self.ladderoptions[ladderid].controlteamminsize = int(args[1])
							self.ladderoptions[ladderid].controlteamminsize = int(args[1])
							self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder control team size changed." )
						elif len(args) == 3: # separate min & max
							if ( not args[2].isdigit() ):
								self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )							
							else:
								self.ladderoptions[ladderid].controlteamminsize = int(args[1])
								self.ladderoptions[ladderid].controlteammaxsize = int(args[2])
								self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder control team size changed." )
					else:
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderchangeallysize":
			if fromwho in self.admins:
				if len(args) > 3 or not args[0].isdigit() or not args[1].isdigit():
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					ladderid = int(args[0])
					if ( ladderid in self.ladderlist ):
						if len(args) == 2: # min = max
							self.ladderoptions[ladderid].allyminsize = int(args[1])
							self.ladderoptions[ladderid].allymaxsize = int(args[1])
							self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder ally size changed." )
						elif len(args) == 3: # separate min & max
							if ( not args[2].isdigit() ):
								self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )							
							else:
								self.ladderoptions[ladderid].allyminsize = int(args[1])
								self.ladderoptions[ladderid].allymaxsize = int(args[2])
								self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder ally size changed." )
					else:
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )						
		if command == "!ladderaddoption":
			if fromwho in self.admins:
				if len(args) != 4 or not args[0].isdigit() or not args[1].isdigit():
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					ladderid = int(args[0])
					if self.db.LadderExists( ladderid ):
						whitelist = int(args[1]) != 0
						keyname = args[2]
						value = args[3]
						if self.db.GetOptionKeyExists(ladderid, not whitelist, keyname ):
							self.notifyuser( socket, fromwho, fromwhere, ispm, "You cannot use blacklist and whitelist at the same time for the same option key." )
						else:
							try:
								self.db.AddOption( ladderid, whitelist, keyname, value )
								message = "blacklist"
								if whitelist:
									message = "whitelist"
								self.notifyuser( socket, fromwho, fromwhere, ispm, "Option added to the " + message + "." )
							except ElementExistsException, e:
								self.notifyuser( socket, fromwho, fromwhere, ispm, "Option already in db" )
								print e
					else:
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
					
		if command == "!ladderremoveoption":
			if ( fromwho in self.admins ):
				if len(args) != 3 or not args[0].isdigit():
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					ladderid = int(args[0])
					if self.db.LadderExists( ladderid ):
						keyname = args[1]
						value = args[2]
						indisabledoptions = self.db.GetOptionKeyExists(ladderid, False, keyname )
						inenabledoptions = self.db.GetOptionKeyExists(ladderid, True, keyname )
						if not indisabledoptions and not inenabledoptions:
							self.notifyuser( socket, fromwho, fromwhere, ispm, "Key doesn't exist in either whitelist and blackist." )
						else:
							if not self.db.GetOptionKeyValueExists( ladderid, inenabledoptions, keyname, value ):
								message = "blacklisted"
								if inenabledoptions:
									message = "whitelisted"
								self.notifyuser( socket, fromwho, fromwhere, ispm, "Value doesn't exist in " + message + " options" )
							else:
								self.db.DeleteOption( ladderid, inenabledoptions, keyname, value )
								message = "blacklist"
								if inenabledoptions:
									message = "whitelist"
								self.notifyuser( socket, fromwho, fromwhere, ispm, "Option removed from the " + message + "." )
					else:
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderlistoptions":
				if len(args) != 1 or not args[0].isdigit():
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					ladderid = int(args[0])
					if self.db.LadderExists( ladderid ):
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder: " + self.db.GetLadderName(ladderid) )
						"""self.notifyuser( socket, fromwho, fromwhere, ispm, "Min control team size: " + str(self.ladderoptions[ladderid].controlteamminsize) )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Max control team size: " + str(self.ladderoptions[ladderid].controlteammaxsize) )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Min ally size: " + str(self.ladderoptions[ladderid].allyminsize) )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Max ally size: " + str(self.ladderoptions[ladderid].allymaxsize) )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Min control team amount: " + str(self.ladderoptions[ladderid].controlteammincount) )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Max control team amount: " + str(self.ladderoptions[ladderid].controlteammaxcount) )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Min ally amount: " + str(self.ladderoptions[ladderid].allymincount) )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Max ally amount: " + str(self.ladderoptions[ladderid].allymaxcount) )
						"""
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Whitelisted options ( if a key is present, no other value except for those listed will be allowed for such key ):" )
						for opt in self.db.GetFilteredOptions( ladderid, True ):
							self.notifyuser( socket, fromwho, fromwhere, ispm, opt.key + ": " + opt.value )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Blacklisted options ( if a value is present for a key, such value won't be allowed ):" )
						for opt in self.db.GetFilteredOptions( ladderid, False ):
							self.notifyuser( socket, fromwho, fromwhere, ispm, opt.key + ": " + opt.value )
					else:
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!score":
			if len(args) > 2:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = -1
				playername = ""
				if len(args) == 1:
					if args[0].isdigit():
						ladderid = int(args[0])
					else:
						playername = args[0]
				if len(args) == 2:
					if not args[0].isdigit():
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
					else:
						ladderid = int(args[0])
						plaeryname = args[1]
				if ladderid != -1 or len(playername) != 0:
					if ladderid != -1 and len(playername) == 0: # print full ladder scores
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Stub" )
					if ladderid == -1 and len(playername) != 0: # print player's scores for all ladders
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Stub" )
					if ladderid != -1 and len(playername) != 0: # print player's score for given ladder
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Stub" )
		if command == "!help":
			self.notifyuser( socket, fromwho, fromwhere, ispm, "Hello, I am a bot to manage and keep stats of ladder games.\nYou can use the following commands:")
			if fromwho in self.app.config["admins"]:
				self.notifyuser( socket, fromwho, fromwhere, ispm, helpstring_admin )
			self.notifyuser( socket, fromwho, fromwhere, ispm, helpstring_user )
		if command == "!laddercopy" and fromwho in self.admins:
			if len(args) < 2:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				source_id = args[0]
				target_name = " ".join(args[1:])
				try:
					self.db.CopyLadder( source_id, target_name )
				except:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Couldn't copy ladder" )
			
	def oncommandfromserver(self,command,args,socket):
		if command == "SAID" and len(args) > 2 and args[2].startswith("!"):
			self.oncommandfromuser(args[1],args[0],False,args[2],args[3:],socket)
		if command == "SAIDPRIVATE" and len(args) > 1 and args[1].startswith("!"):
			self.oncommandfromuser(args[0],"PM",True,args[1],args[2:],socket)
		if command == "FORCELEAVECHANNEL" and len(args) > 1:
			if args[0] in self.channels:
				self.channels.remove(args[0])
				self.app.config["channelautojoinlist"] = ','.join(self.channels)
				self.app.SaveConfig()
				
	def updatestatus(self,socket):
		socket.send("MYSTATUS %i\n" % int(int(0)+int(0)*2))	
	def onloggedin(self,socket):
		self.updatestatus(socket)	
