from colors import *
from ParseConfig import *
import commands
import thread
import os
import sys
import signal
import traceback
import subprocess
import sqlalchemy
def pm(s,p,m):
	try:
		print yellow+"PM To:%s, Message: %s" %(p,m) + normal
		s.send("SAYPRIVATE %s %s\n" %(p,m))
	except:
		pass
def saychannel( socket, channel, message ):
		print purple+"Channel :%s, Message: %s" %(channel,message) + normal
		socket.send("SAY " + channel + " " + message + "\n")
class OptionEntry:
	 def __init__(self):
	 	self.valuelist = []
class LadderOptions:
	 def __init__(self):
	 	self.modname = ""
	 	self.controlteamminsize = 1
	 	self.controlteammaxsize = 1
	 	self.allymaxsize = 1
	 	self.allyminsize = 1
	 	self.allowedoptions = dict() # option path -> list of allowed values
	 	self.restrictedoptions = dict() # option path -> list of denied value
	 	self.allowedmaps = [] # list of allowed map names
	 	self.restrictedmaps = [] # list of denied map names
class LadderMatch:
	def __init__(self):
		self.timestamp = 0
		self.winnerid = -1
		self.playerids = []
		self.teams
class LadderScores:
	def __init__(self):
		self.playerscores = [] # player id -> score
class Main:
	botpid = dict() # slot -> bot pid
	botstatus = dict() # slot -> bot already spawned
	battleswithbots = dict() # battle id -> bot already in
	ladderlist = dict() # id -> ladder name
	ladderoptions = dict() # id -> ladder options
	
	sql = sqlalchemy.create_engine('sqlite:///:memory:', echo=True)
	def botthread(self,slot,battleid,ladderid,ist):
		try:
			d = dict()
			d.update([("serveraddr",self.app.config["serveraddr"])])
			d.update([("serverport",self.app.config["serverport"])])
			d.update([("admins",self.app.config["admins"])])
			d.update([("nick",self.app.config["nick"])+str(slot)])
			d.update([("password",self.app.config["password"])])
			d.update([("plugins","channels,ladderbot,help")])
			d.update([("bans",self.app.config["bans"])])
			d.update([("battleid",str(battleid))])
			d.update([("ladderid",str(ladderid))])
			writeconfigfile(nick+".cfg",d)
			p = subprocess.Popen(("python","Main.py","-c", "%s" % (nick+".cfg")),stdout=sys.stdout)
			self.bots[slot] = p.pid
			#print self.bots
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
	def notifyuser( self, socket, fromwho, fromwhere, ispm, message ):
		if fromwhere == "main":
			ispm = true
		if not ispm:
			saychannel( socket, fromwhere, message )
		else:
			pm( socket, fromwho, message )
	def spawnbot( self,  socket, battleid, ladderid ):	
		slot = len(botstatus)
		self.threads.append(thread.start_new_thread(self.botthread,(slot,socket,battleid,ladderid,self)))
		self.botstatus[slot] = True
	def oncommandfromuser(self,fromwho,fromwhere,ispm,command,args,socket):
		if fromwho == self.app.config["nick"]:
			return
		if command == "!ladder":
			ladderid = -1
			if len(args) > 1:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax or command not found, use !help for a list of available commands and their usage." )
			else:
				if ( args[0].isdigit() ):
					ladderid = int(args[0])
				try:
					battleid = self.users[self.args[0]].battleid
					if ( battleid == -1 ):
						self.notifyuser( socket, fromwho, fromwhere, ispm, "You are not in a battle." )
					else:
						if ( battleswithbots[battleid] == True ):
							self.notifyuser( socket, fromwho, fromwhere, ispm, "A ladder bot is already present in your battle." )
						else:
							if ( laderid == -1 or ladderid in self.ladderlist ):
								self.spawnbot( self, socket, battleid, ladderid )
							else:
								self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
				except:
					pass
		if command == "!ladderjoinchannel":
			if ( fromwho in self.app.config["admins"]):
				if len(args) < 1:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					channel = " ".join(args[0:])
					socket.send("JOIN " + channel + "\n")
					if not channel in self.app.config["channelautojoinlist"]:
						self.app.config["channelautojoinlist"].append(channel)
						self.app.SaveConfig()
		if command == "!ladderleavechannel":
			if ( fromwho in self.app.config["admins"]):
				if len(args) != 1:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					channel = args[0]
					socket.send("LEAVE " + channel + "\n")
					if channel in self.app.config["channelautojoinlist"]:
						self.app.config["channelautojoinlist"].remove(channel)
						self.app.SaveConfig()		
		if command == "!ladderlist":
			self.notifyuser( socket, fromwho, fromwhere, ispm, "Available ladders, format name: ID:" )
			for i in self.ladderlist:
				self.notifyuser( socket, fromwho, fromwhere, ispm, self.ladderlist[i] + ": " + str(i) )
		if command == "!ladderadd":
			if ( fromwho in self.app.config["admins"] ):
				if len(args) < 1:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder name can't be empty." )
				else:
					ladderid = len(self.ladderlist)
					self.ladderlist[ladderid] = " ".join(args[0:])
					self.ladderoptions[ladderid] = LadderOptions()
					self.notifyuser( socket, fromwho, fromwhere, ispm, "New ladder created, ID: " + str(ladderid) )
		if command == "!ladderremove":
			if ( fromwho in self.app.config["admins"] ):
				if len(args) != 1 or not args[0].isdigit():
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					ladderid = int(args[0])
					if ( ladderid in self.ladderlist ):
						del self.ladderlist[ladderid]
						del self.ladderoptions[ladderid]
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder removed." )
					else:
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderchangemod":
			if ( fromwho in self.app.config["admins"]):
				if len(args) < 2 or not args[0].isdigit():
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					ladderid = int(args[0])
					if ( ladderid in self.ladderlist ):
						self.ladderoptions[ladderid].modname = " ".join(args[1:])
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder mod changed." )
					else:
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderchangecontrolteamsize":
			if ( fromwho in self.app.config["admins"]):
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
			if ( fromwho in self.app.config["admins"]):
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
			if ( fromwho in self.app.config["admins"]):
				if len(args) != 4 or not args[0].isdigit() or not args[1].isdigit():
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					ladderid = int(args[0])
					if ( ladderid in self.ladderlist ):
						whitelist = int(args[1]) != 0
						keyname = args[2]
						value = args[3]
						if whitelist:
							if ( keyname in self.ladderoptions[ladderid].restrictedoptions ):
								self.notifyuser( socket, fromwho, fromwhere, ispm, "You cannot use blacklist and whitelist at the same time for the same option key." )
							else:
								if keyname in  self.ladderoptions[ladderid].allowedoptions:
									currentvalues = self.ladderoptions[ladderid].allowedoptions[keyname]
								else:
									currentvalues = []
								if ( not value in currentvalues ):
									currentvalues.append(value)
									self.ladderoptions[ladderid].allowedoptions[keyname] = currentvalues
									self.notifyuser( socket, fromwho, fromwhere, ispm, "Option added to the whitelist." )
						else:
							if( keyname in self.ladderoptions[ladderid].allowedoptions ):
								self.notifyuser( socket, fromwho, fromwhere, ispm, "You cannot use blacklist and whitelist at the same time for the same option key." )
							else:
								if keyname in self.ladderoptions[ladderid].restrictedoptions:
									currentvalues = self.ladderoptions[ladderid].restrictedoptions[keyname]
								else:
									currentvalues = []
								if ( not value in currentvalues ):
									currentvalues.append(value)
									self.ladderoptions[ladderid].restrictedoptions[keyname] = currentvalues
									self.notifyuser( socket, fromwho, fromwhere, ispm, "Option added to the blacklist." )
					else:
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderremoveoption":
			if ( fromwho in self.app.config["admins"] ):
				if len(args) != 3 or not args[0].isdigit():
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					ladderid = int(args[0])
					if ( ladderid in self.ladderlist ):
						keyname = args[1]
						value = args[2]
						indisabledoptions = False
						inenabledoptions = False
						if keyname in self.ladderoptions[ladderid].restrictedoptions:
							indisabledoptions = True					
						if keyname in self.ladderoptions[ladderid].allowedoptions:
							inenabledoptions = True
						if not indisabledoptions and not inenabledoptions:
							self.notifyuser( socket, fromwho, fromwhere, ispm, "Key doesn't exist in both whitelist and blackist." )
						else:
							currentvalues = dict()
							if indisabledoptions:
								currentvalues = self.ladderoptions[ladderid].restrictedoptions[keyname]
							else:
								currentvalues = self.ladderoptions[ladderid].allowedoptions[keyname]
							if not value in currentvalues:
								message = "blacklisted"
								if inenabledoptions:
									message = "whitelisted"
								self.notifyuser( socket, fromwho, fromwhere, ispm, "Value doesn't exist in " + message + " options" )
							else:
								currentvalues.remove(value)
								if inenabledoptions:
									if len(currentvalues) == 0:
										del self.ladderoptions[ladderid].allowedoptions[keyname]
									else:
										self.ladderoptions[ladderid].allowedoptions[keyname] = currentvalues
									self.notifyuser( socket, fromwho, fromwhere, ispm, "Option removed from the whitelist." )
								else:
									if len(currentvalues) == 0:
										del self.ladderoptions[ladderid].restrictedoptions[keyname]
									else:
										self.ladderoptions[ladderid].restrictedoptions[keyname] = currentvalues
									self.notifyuser( socket, fromwho, fromwhere, ispm, "Option removed from the blacklist." )
					else:
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderlistoptions":
				if len(args) != 1 or not args[0].isdigit():
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					ladderid = int(args[0])
					if ( ladderid in self.ladderlist ):
						whitelist = self.ladderoptions[ladderid].allowedoptions
						blacklist = self.ladderoptions[ladderid].restrictedoptions
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder: " + self.ladderlist[ladderid] )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "modname: " + self.ladderoptions[ladderid].modname )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Min control team size: " + str(self.ladderoptions[ladderid].controlteamminsize) )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Max control team size: " + str(self.ladderoptions[ladderid].controlteammaxsize) )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Min ally size: " + str(self.ladderoptions[ladderid].allyminsize) )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Max ally size: " + str(self.ladderoptions[ladderid].allymaxsize) )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Whitelisted options ( if a key is present, no other value except for those listed will be allowed for such key ):" )
						for key in whitelist:
							allowedvalues = whitelist[key]
							for value in allowedvalues:
								self.notifyuser( socket, fromwho, fromwhere, ispm, key + ": " + value )
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Blacklisted options ( if a value is present for a key, such value won't be allowed ):" )
						for key in blacklist:
							disabledvalues = blacklist[key]
							for value in disabledvalues:
								self.notifyuser( socket, fromwho, fromwhere, ispm, key + ": " + value )						
					else:
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderaddmap":
			if ( fromwho in self.app.config["admins"] ):
				if len(args) < 3 or not args[0].isdigit() or not args[1].isdigit():
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					ladderid = int(args[0])
					if ( ladderid in self.ladderlist ):
						whitelist = int(args[1]) != 0
						mapname = " ".join(args[2:])
						if whitelist:
							if (len(self.ladderoptions[ladderid].restrictedmaps) != 0 ):
								self.notifyuser( socket, fromwho, fromwhere, ispm, "You cannot use blacklist and whitelist at the same time for maps." )
							else:
								if ( not mapname in self.ladderoptions[ladderid].allowedmaps ):
									self.ladderoptions[ladderid].allowedmaps.append(mapname)
									self.notifyuser( socket, fromwho, fromwhere, ispm, "Map added to the whitelist." )
						else:
							if( len(self.ladderoptions[ladderid].allowedmaps) != 0 ):
								self.notifyuser( socket, fromwho, fromwhere, ispm, "You cannot use blacklist and whitelist at the same time for maps." )
							else:
								if ( not mapname in self.ladderoptions[ladderid].restrictedmaps ):
									self.ladderoptions[ladderid].restrictedmaps.append(mapname)
									self.notifyuser( socket, fromwho, fromwhere, ispm, "Map added to the blacklist." )
					else:
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderremovemap":
			if ( fromwho in self.app.config["admins"] ):
				if len(args) < 2 or not args[0].isdigit():
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
				else:
					ladderid = int(args[0])
					if ( ladderid in self.ladderlist ):
						mapname = " ".join(args[1:])
						indisabledmaps = False
						inenabledmaps = False
						if mapname in self.ladderoptions[ladderid].restrictedmaps:
							indisabledmaps = True
						if mapname in self.ladderoptions[ladderid].allowedmaps:
							inenabledmaps = True
						if not indisabledmaps and not inenabledmaps:
							self.notifyuser( socket, fromwho, fromwhere, ispm, "Map doesn't exist in both whitelist and blackist." )
						else:
							if indisabledmaps:
								self.ladderoptions[ladderid].restrictedmaps.remove(mapname)
								self.notifyuser( socket, fromwho, fromwhere, ispm, "Map removed from blacklist." )
							else:
								self.ladderoptions[ladderid].allowedmaps.remove(mapname)
								self.notifyuser( socket, fromwho, fromwhere, ispm, "Map removed from whitelist." )
					else:
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderlistmaps":
			if len(args) != 1 or not args[0].isdigit():
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = int(args[0])
				if ( ladderid in self.ladderlist ):
					indisabledmaps = False
					indenabledmaps = False
					if len(self.ladderoptions[ladderid].restrictedmaps) > 0:
						indisabledmaps = True
					if len(self.ladderoptions[ladderid].allowedmaps) > 0:
						indenabledmaps = True
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder: " + self.ladderlist[ladderid] )
					if not indisabledmaps and not indenabledmaps:
						self.notifyuser( socket, fromwho, fromwhere, ispm, "No map restrictions are in place." )
					else:
						maplist = []
						if indisabledmaps:
							self.notifyuser( socket, fromwho, fromwhere, ispm, "Blacklisted maps:" )
							maplist = self.ladderoptions[ladderid].restrictedmaps
						else:
							self.notifyuser( socket, fromwho, fromwhere, ispm, "Whitelisted maps:" )
							maplist = self.ladderoptions[ladderid].allowedmaps
						for mapname in maplist:
							self.notifyuser( socket, fromwho, fromwhere, ispm, mapname )
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
			self.notifyuser( socket, fromwho, fromwhere, ispm, "Hello, I am a bot to manage and keep stats of ladder games." )
			self.notifyuser( socket, fromwho, fromwhere, ispm, "You can use the following commands:" )
			if fromwho in self.app.config["admins"]:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladderjoinchannel channelname password : make the bot join a new channel and add to the autojoin list" )
				self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladderleavechannel channelname : make the bot leave a chanel and remove it from the autojoin list" )
				self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladderadd laddername : creates a new ladder" )
				self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladderremove ladderID : deletes a ladder" )
				self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladderchangemod ladderID modname : sets the mod for given ladder ID" )
				self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladderchangecontrolteamsize ladderID value : sets the control team size (player ID) used by the ladder" )
				self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladderchangecontrolteamsize ladderID min max : sets the control team size (player ID) used by the ladder" )
				self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladderchangeallysize ladderID value : sets the ally team size used by the ladder" )
				self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladderchangeallysize ladderID min max : sets the ally team size used by the ladder" )
				self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladderaddoption ladderID blacklist/whitelist optionkey optionvalue : adds a new rule to the ladder, blacklist/whitelist is boolean and 1 means whitelist, a given key cannot have a whitelist and blacklist at the same time" )
				self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladderremoveoption ladderID optionkey optionvalue : removes optionvalue from the ladder rules, if the optionkey has no values anymore it will be automatically removed" )
				self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladderaddmap ladderID blacklist/whitelist mapname : adds a new map rule to the ladder, blacklist/whitelist is boolean and 1 means whitelist, a ladder cannot have a map whitelist and blacklist at the same time" )
				self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladderremovemap ladderID mapname : removes mapname from the ladder map rules" )
			self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladderlist : lists available ladders with their IDs" )	
			self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladder : requests a bot to join your current game to monitor and submit scores" )	
			self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladder ladderID: requests a bot to join your current game to monitor and submit scores got given ladderID" )	
			self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladderlistoptions ladderID : lists enforced options for given ladderID" )	
			self.notifyuser( socket, fromwho, fromwhere, ispm, "!ladderlistmaps ladderID : lists enforced maps for given ladderID" )
			self.notifyuser( socket, fromwho, fromwhere, ispm, "!score ladderID : lists scores for all the players for the given ladderID" )			
			self.notifyuser( socket, fromwho, fromwhere, ispm, "!score playername : lists scores for the given player in all ladders" )
			self.notifyuser( socket, fromwho, fromwhere, ispm, "!score ladderID playername : lists score for the given player for the given ladderID" )
	def oncommandfromserver(self,command,args,socket):
		if command == "SAID" and len(args) > 2 and args[2].startswith("!"):
			self.oncommandfromuser(args[1],args[0],False,args[2],args[3:],socket)
		if command == "SAIDPRIVATE" and len(args) > 1 and args[1].startswith("!"):
			self.oncommandfromuser(args[0],"PM",True,args[1],args[2:],socket)
		if command == "FORCELEAVECHANNEL" and len(args) > 1:
			if args[0] in self.app.config["channelautojoinlist"]:
				self.app.config["channelautojoinlist"].remove(args[0])
				self.app.SaveConfig()
	def updatestatus(self,socket):
		socket.send("MYSTATUS %i\n" % int(int(0)+int(0)*2))	
	def onloggedin(self,socket):
		self.updatestatus(socket)	
