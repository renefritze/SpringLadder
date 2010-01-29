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

helpstring_ladder_admin = """!ladderjoinchannel channelname password: joins set channel and stores for automatic join
!ladderleavechannel channelname : leaves set channel and removes it from autojoin list
!ladderchangeaicount ladderID value : sets the AI count used by the ladder
!ladderchangeaicount ladderID min max : sets the AI count used by the ladder
!ladderchangecontrolteamsize ladderID value : sets the control team size (player ID) used by the ladder
!ladderchangecontrolteamsize ladderID min max : sets the control team size (player ID) used by the ladder
!ladderchangecontrolteamcount ladderID value : sets the control team count (player ID) used by the ladder
!ladderchangecontrolteamcount ladderID min max : sets the control team count (player ID) used by the ladder
!ladderchangeallysize ladderID value : sets the ally size used by the ladder
!ladderchangeallysize ladderID min max : sets the ally size used by the ladder
!ladderchangeallycount ladderID value : sets the ally count used by the ladder
!ladderchangeallycount ladderID min max : sets the ally count used by the ladder
!ladderaddoption ladderID blacklist/whitelist optionkey optionvalue : adds a new rule to the ladder, blacklist/whitelist is boolean and 1 means whitelist, a given key cannot have a whitelist and blacklist at the same time
!ladderremoveoption ladderID optionkey optionvalue : removes optionvalue from the ladder rules, if the optionkey has no values anymore it will be automatically removed
!ladderlistrankingalgos : list all available ranking algorithms by name
!laddersetrankingalgo ladderID algoName :set the used algorithm for ranking, currently switching algo on non-empty ladder will not recalc past results with new algo
!ladderdeletematch ladderID matchID: delete a match and all associated data from db, forces a recalculation of entire history of rankings for that ladder
!ladderbanuser ladderID username [time] : ban username from participating in any match on ladder ladderID for given amount of time (optional,floats, format: [D:]H )
!ladderunbanuser ladderID username : unban username from participating in any match on ladder ladderID
!ladderlistbans ladderID"""

helpstring_global_admin = """!ladderadd laddername : creates a new ladder
!ladderremove ladderID : deletes a ladder
!laddercopy source_id target_name : copy ladder with source_id to new ladder named target_name including all options
!ladderaddladderadmin ladderID username : add a new (local) admin to the ladder with LadderID
!ladderaddglobaladmin username : add a new global admin
!ladderdeleteladderadmin ladderID username : delete new (local) admin from the ladder with LadderID
!ladderdeleteglobaladmin username : delete global admin
!ladderbanuserglobal username [time] : ban username from participating in any match on any ladder for given amount of time (optional,floats, format: [D:]H )
!ladderunbanuserglobal username : unban username from participating in any match on any ladder"""

helpstring_user = """!ladderlist : lists available ladders with their IDs
!ladder : requests a bot to join your current game to monitor and submit scores
!ladder ladderID: requests a bot to join your current game to monitor and submit scores got given ladderID
!ladderlistoptions ladderID : lists enforced options for given ladderID
!score ladderID : lists scores for all the players for the given ladderID
!score playername : lists scores for the given player in all ladders
!score ladderID playername : lists score for the given player for the given ladderID
!ladderlistmatches ladderID : list all matches for ladderId, newest first"""

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
	botstatus = [] # slot -> bot already spawned
	battleswithbots = [] # battle id -> bot already in
	ladderlist = dict() # id -> ladder name
	ladderoptions = dict() # id -> ladder options

	def botthread(self,slot,battleid,fromwho,ladderid):
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
			d.update([("fromwho",fromwho)])
			d.update([("alchemy-uri",self.app.config["alchemy-uri"])])
			d.update([("alchemy-verbose",self.app.config["alchemy-verbose"])])
			d.update([("springdedclientpath",self.app.config["springdedclientpath"])])
			if "springdatapath" in self.app.config:
				d.update([("springdatapath",self.app.config["springdatapath"])])
			writeconfigfile(nick+".cfg",d)
			p = subprocess.Popen(("python","Main.py","-c", "%s" % (nick+".cfg")),stdout=sys.stdout)
			self.botpid[slot] = p.pid
			p.wait()
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
		self.db = LadderDB( parselist(self.app.config["alchemy-uri"],",")[0], parselist(self.app.config["alchemy-verbose"],",")[0] )

	def notifyuser( self, socket, fromwho, fromwhere, ispm, message ):
		if fromwhere == "main":
			ispm = true
		if not ispm:
			saychannel( socket, fromwhere, message )
		else:
			pm( socket, fromwho, message )

	def sayPermissionDenied(self, socket, command, username,fromwhere, ispm  ):
		msg = 'You do not have sufficient access right to execute %s on this bot\n' %( command )
		self.notifyuser( socket, username, fromwhere, ispm, msg )
	
	def spawnbot( self,  socket, battleid, fromwho, ladderid ):
		slot = len(self.botstatus)
		notice("spawning " + self.app.config["nick"]+str(slot) + " to join battle " + str(battleid) + " with ladder " + str(ladderid))
		self.threads.append(thread.start_new_thread(self.botthread,(slot,battleid,fromwho,ladderid)))

	def oncommandfromuser(self,fromwho,fromwhere,ispm,command,args,socket):
		if fromwho == self.app.config["nick"]:
			return
		if len(command) > 0 and command[0] == "!":
			if not self.db.AccessCheck( -1, fromwho, Roles.User ):
				self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
				#log
				return
		else:
			return

		# !TODO refactor to use function dict
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
					if not self.db.AccessCheck( ladderid, fromwho, Roles.User ):
						self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
						#log
						return
					if ( battleid in self.battleswithbots ):
						self.notifyuser( socket, fromwho, fromwhere, ispm, "A ladder bot is already present in your battle." )
					else:
						if ( ladderid == -1 or self.db.LadderExists( ladderid ) ):
							self.spawnbot( socket, battleid, fromwho, ladderid )
						else:
							self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderjoinchannel":
			if not self.db.AccessCheck( -1, fromwho, Roles.GlobalAdmin ):
				self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
				#log
				return
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
			if not self.db.AccessCheck( -1, fromwho, Roles.GlobalAdmin ):
				self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
				#log
				return
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
			if not self.db.AccessCheck( -1, fromwho, Roles.GlobalAdmin ):
				self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
				#log
				return
			if len(args) < 1:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder name can't be empty." )
			else:
				try:
					laddername = " ".join(args[0:])
					ladderid = self.db.AddLadder( laddername )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "New ladder created, ID: " + str(ladderid) )
				except ElementExistsException, e:
					error(e)
		if command == "!ladderremove":
			if not self.db.AccessCheck( -1, fromwho, Roles.GlobalAdmin ):
				self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
				#log
				return
			if len(args) != 1 or not args[0].isdigit():
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = int(args[0])
				try:
					self.db.RemoveLadder( args[0] )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder removed." )
				except ElementNotFoundException, e:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderchangeaicount":
			if len(args) > 3 or not args[0].isdigit() or not args[1].isdigit():
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = int(args[0])
				try:
					ladder = self.db.GetLadder( ladderid )
					if not self.db.AccessCheck( ladderid, fromwho, Roles.LadderAdmin ):
						self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
						#log
						return
					ladder.min_ai_count = int(args[1])
					if len(args) == 2: # min = max
						ladder.max_ai_count = int(args[1])
					elif len(args) == 3: # separate min & max
						if args[2] < args[1]:
							self.notifyuser( socket, fromwho, fromwhere, ispm, "max ai count < min! not changed." )
							return
						ladder.max_ai_count = int(args[2])
					self.db.SetLadder( ladder )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder ai count changed." )
				except ElementNotFoundException, e:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderchangecontrolteamsize":
			if len(args) > 3 or not args[0].isdigit() or not args[1].isdigit():
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = int(args[0])
				try:
					ladder = self.db.GetLadder( ladderid )
					if not self.db.AccessCheck( ladderid, fromwho, Roles.LadderAdmin ):
						self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
						#log
						return
					ladder.min_team_size = int(args[1])
					if len(args) == 2: # min = max
						ladder.max_team_size = int(args[1])
					elif len(args) == 3: # separate min & max
						if args[2] < args[1]:
							self.notifyuser( socket, fromwho, fromwhere, ispm, "max control team size < min! not changed." )
							return
						ladder.max_team_size = int(args[2])
					self.db.SetLadder( ladder )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder control team size changed." )
				except ElementNotFoundException, e:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderchangeallysize":
			if len(args) > 3 or not args[0].isdigit() or not args[1].isdigit():
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = int(args[0])
				try:
					ladder = self.db.GetLadder( ladderid )
					if not self.db.AccessCheck( ladderid, fromwho, Roles.LadderAdmin ):
						self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
						#log
						return
					ladder.min_ally_size = int(args[1])
					if len(args) == 2: # min = max
						ladder.max_ally_size = int(args[1])
					elif len(args) == 3: # separate min & max
						if args[2] < args[1]:
							self.notifyuser( socket, fromwho, fromwhere, ispm, "max ally size < min! not changed." )
							return
						ladder.max_ally_size = int(args[2])
					self.db.SetLadder( ladder )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder ally size changed." )
				except ElementNotFoundException, e:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderchangecontrolteamcount":
			if len(args) > 3 or not args[0].isdigit() or not args[1].isdigit():
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = int(args[0])
				try:
					ladder = self.db.GetLadder( ladderid )
					if not self.db.AccessCheck( ladderid, fromwho, Roles.LadderAdmin ):
						self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
						#log
						return
					ladder.min_team_count = int(args[1])
					if len(args) == 2: # min = max
						ladder.max_team_count = int(args[1])
					elif len(args) == 3: # separate min & max
						if args[2] < args[1]:
							self.notifyuser( socket, fromwho, fromwhere, ispm, "max control team count < min! not changed." )
							return
						ladder.max_team_count = int(args[2])
					self.db.SetLadder( ladder )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder control team count changed." )
				except ElementNotFoundException, e:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderchangeallycount":
			if len(args) > 3 or not args[0].isdigit() or not args[1].isdigit():
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = int(args[0])
				try:
					ladder = self.db.GetLadder( ladderid )
					if not self.db.AccessCheck( ladderid, fromwho, Roles.LadderAdmin ):
						self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
						#log
						return
					ladder.min_ally_count = int(args[1])
					if len(args) == 2: # min = max
						ladder.max_ally_count = int(args[1])
					elif len(args) == 3: # separate min & max
						if args[2] < args[1]:
							self.notifyuser( socket, fromwho, fromwhere, ispm, "max ally count < min! not changed." )
							return
						ladder.max_ally_count = int(args[2])
					self.db.SetLadder( ladder )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Ladder ally count changed." )
				except ElementNotFoundException, e:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderaddoption":
			if len(args) < 4 or not args[0].isdigit() or not args[1].isdigit():
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = int(args[0])
				if self.db.LadderExists( ladderid ):
					if not self.db.AccessCheck( ladderid, fromwho, Roles.LadderAdmin ):
						self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
						#log
						return
					whitelist = int(args[1]) != 0
					keyname = args[2]
					value = " ".join(args[3:])
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
				else:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!ladderremoveoption":
			if len(args) < 3 or not args[0].isdigit():
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = int(args[0])
				if self.db.LadderExists( ladderid ):
					if not self.db.AccessCheck( ladderid, fromwho, Roles.LadderAdmin ):
						self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
						#log
						return
					keyname = args[1]
					value = " ".join(args[2:])
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
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Min AIs in a Match ( how many AIs ): " + str(self.db.GetLadderOption( ladderid, "min_ai_count" )) )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Max Ais in a Match ( how many AIs ): " + str(self.db.GetLadderOption( ladderid, "max_ai_count" )) )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Min Players in a Team ( sharing control ): " + str(self.db.GetLadderOption( ladderid, "min_team_size" )) )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Max Players in a Team ( sharing control ): " + str(self.db.GetLadderOption( ladderid, "max_team_size" )) )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Min Teams in an Ally ( being allied ): " + str(self.db.GetLadderOption( ladderid, "min_ally_size" )) )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Max Teams in an Ally ( being allied ): " + str(self.db.GetLadderOption( ladderid, "max_team_size" )) )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Min Teams in a Match ( how many Teams ): " + str(self.db.GetLadderOption( ladderid, "min_team_count" )) )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Max Teams in a Match ( how many Teams ): " + str(self.db.GetLadderOption( ladderid, "max_team_count" )) )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Min Alliances in a Match ( how many Allys ): " + str(self.db.GetLadderOption( ladderid, "min_ally_count" )) )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Max Alliances in a Match ( how many Allys ): " + str(self.db.GetLadderOption( ladderid, "max_ally_count" )) )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Whitelisted options ( if a key is present, no other value except for those listed will be allowed for such key ):" )
					for opt in self.db.GetFilteredOptions( ladderid, True ):
						self.notifyuser( socket, fromwho, fromwhere, ispm, opt.key + ": " + opt.value )
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Blacklisted options ( if a value is present for a key, such value won't be allowed ):" )
					for opt in self.db.GetFilteredOptions( ladderid, False ):
						self.notifyuser( socket, fromwho, fromwhere, ispm, opt.key + ": " + opt.value )
				else:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid ladder ID." )
		if command == "!score":
			if not self.db.AccessCheck( -1, fromwho, Roles.User ):
				self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
				#log
				return
			if len(args) > 2:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = -1
				playername = ""
				rep = ''
				if len(args) == 1:
					if args[0].isdigit():
						ladderid = int(args[0])
						rep = GlobalRankingAlgoSelector.GetPrintableRepresentation( self.db.GetRanks( ladderid ), self.db )
					else:
						playername = args[0]
						rep = GlobalRankingAlgoSelector.GetPrintableRepresentationPlayer( self.db.GetPlayerRanks( playername ), self.db )
					self.notifyuser( socket, fromwho, fromwhere, ispm, rep )

				elif len(args) == 2:
					if not args[0].isdigit():
						self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
					else:
						ladderid = int(args[0])
						playername = args[1]
						rep = GlobalRankingAlgoSelector.GetPrintableRepresentation( self.db.GetRanks( ladderid, playername ), self.db )
						self.notifyuser( socket, fromwho, fromwhere, ispm, rep )
		if command == "!ladderhelp":
			self.notifyuser( socket, fromwho, fromwhere, ispm, "Hello, I am a bot to manage and keep stats of ladder games.\nYou can use the following commands:")
			if self.db.AccessCheck( -1, fromwho, Roles.GlobalAdmin ):
				self.notifyuser( socket, fromwho, fromwhere, ispm, helpstring_global_admin )
			if self.db.AccessCheck( -1, fromwho, Roles.LadderAdmin ):
				self.notifyuser( socket, fromwho, fromwhere, ispm, helpstring_ladder_admin )
			self.notifyuser( socket, fromwho, fromwhere, ispm, helpstring_user )
		if command == "!laddercopy":
			if not self.db.AccessCheck( -1, fromwho, Roles.GlobalAdmin ):
				self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
				#log
				return
			if len(args) < 2:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				source_id = args[0]
				target_name = " ".join(args[1:])
				try:
					self.db.CopyLadder( source_id, target_name )
				except:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Couldn't copy ladder" )
		if command == "!ladderaddglobaladmin":
			if not self.db.AccessCheck( -1, fromwho, Roles.Owner ):
				self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
				#log
				return
			if len(args) < 1:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				username = args[0]
				try:
					self.db.AddGlobalAdmin( username )
				except:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Couldn't add global admin" )
		if command == "!ladderaddladderadmin":
			if not self.db.AccessCheck( -1, fromwho, Roles.GlobalAdmin ):
				self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
				#log
				return
			if len(args) < 2:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = args[0]
				username = args[1]
				try:
					self.db.AddLadderAdmin( ladderid, username )
				except ElementNotFoundException, e:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Couldn't add ladder admin: " + str(e) )
		if command == "!ladderdeleteglobaladmin":
			if not self.db.AccessCheck( -1, fromwho, Roles.Owner ):
				self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
				#log
				return
			if len(args) < 1:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				username = args[0]
				try:
					self.db.DeleteGlobalAdmin( username )
				except:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Couldn't delete global admin" )
		if command == "!ladderdeleteladderadmin":
			if not self.db.AccessCheck( -1, fromwho, Roles.GlobalAdmin ):
				self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
				#log
				return
			if len(args) < 2:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = args[0]
				username = args[1]
				try:
					self.db.DeleteLadderAdmin( ladderid, username )
				except:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Couldn't delete ladder admin" )
		if command == "!ladderlistrankingalgos":
			if len(args) > 0:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				self.notifyuser( socket, fromwho, fromwhere, ispm, GlobalRankingAlgoSelector.ListRegisteredAlgos() )
		if command == "!laddersetrankingalgo":
			if len(args) < 2:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = args[0]
				algoname = args[1]
				try:
					GlobalRankingAlgoSelector.GetInstance( algoname ) # algo unknonw -> excpetion raised
					self.db.SetLadderRankingAlgo( ladderid, algoname )
				except ElementNotFoundException, e:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Couldn't set ranking algo: " + str(e) )
		if command == "!ladderlistmatches":
			if len(args) != 1:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = args[0]
				try:
					matches = self.db.GetMatches( ladderid )
					res = ''
					for m in matches:
						res += 'Match no. %d (%s)\n'%(m.id,m.date)
					self.notifyuser( socket, fromwho, fromwhere, ispm, res )
				except ElementNotFoundException, e:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Error: " + str(e) )
		if command == "!ladderdeletematch":
			if len(args) != 2:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = int(args[0])
				match_id = int(args[1])
				if not self.db.AccessCheck( ladderid, fromwho, Roles.LadderAdmin ):
						self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
							#log
						return

				try:
					self.db.DeleteMatch( ladderid, match_id )
				except ElementNotFoundException, e:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Error: " + str(e) )
		if command == "!ladderbanuserglobal":
			if len(args) < 1:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				username = args[0]
				if len(args) == 2:
					t_fields = args[1].split(':')
					if len( t_fields ) > 1:
						days  = float(t_fields[0])
						hours = float(t_fields[1])
					else:
						days = 0
						hours = float(t_fields[0])
					t_delta = timedelta( days=days, hours=hours )
				else:
					t_delta = timedelta.max
				if not self.db.AccessCheck( -1, fromwho, Roles.GlobalAdmin ):
						self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
							#log
						return
				try:
					self.db.BanPlayer( -1, username, t_delta )
				except ElementNotFoundException, e:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Error: " + str(e) )
		if command == "!ladderunbanuserglobal":
			if len(args) != 1:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				username = args[0]
				if not self.db.AccessCheck( -1, fromwho, Roles.GlobalAdmin ):
					self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
						#log
					return
				try:
					self.db.UnbanPlayer( username )
				except ElementNotFoundException, e:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Error: " + str(e) )
		if command == "!ladderbanuser":
			if len(args) < 2:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = args[0]
				username = args[1]
				if len(args) == 3:
					t_fields = args[2].split(':')
					if len( t_fields ) > 1:
						days  = float(t_fields[0])
						hours = float(t_fields[1])
					else:
						days = 0
						hours = float(t_fields[0])
					t_delta = timedelta( days=days, hours=hours )
				else:
					t_delta = timedelta.max
				if not self.db.AccessCheck( ladderid, fromwho, Roles.LadderAdmin ):
						self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
							#log
						return
				try:
					self.db.BanPlayer( ladderid, username, t_delta )
				except ElementNotFoundException, e:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Error: " + str(e) )
		if command == "!ladderunbanuser":
			if len(args) < 2:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Invalid command syntax, check !help for usage." )
			else:
				ladderid = args[0]
				username = args[1]
				if not self.db.AccessCheck( ladderid, fromwho, Roles.LadderAdmin ):
						self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
							#log
						return
				try:
					self.db.UnbanPlayer( username, ladderid )
				except ElementNotFoundException, e:
					self.notifyuser( socket, fromwho, fromwhere, ispm, "Error: " + str(e) )
		if command == "!ladderlistbans":
			if len(args) < 1:
				ladderid = -1
			else:
				ladderid = args[0]
			if not self.db.AccessCheck( ladderid, fromwho, Roles.LadderAdmin ):
					self.sayPermissionDenied( socket, command, fromwho, fromwhere, ispm )
						#log
					return
			try:
				bans = self.db.GetBansPerLadder( ladderid )
				msg = ''
				s = self.db.sessionmaker() #not nice, but needed for lazy load?!?
				s.add_all( bans )
				for b in bans:
					msg += str(b) + '\n'
				self.notifyuser( socket, fromwho, fromwhere, ispm, msg )
				s.close()
			except ElementNotFoundException, e:
				self.notifyuser( socket, fromwho, fromwhere, ispm, "Error: " + str(e) )
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
		if command == "ADDUSER" and len(args) > 0:
			name = args[0]
			basebotname = self.app.config["nick"]
			if name.startswith(basebotname):
				name = name[len(basebotname):] # truncate prefix
				if name.isdigit():
					self.botstatus.append(int(name))
		if command == "REMOVEUSER" and len(args) > 0:
			name = args[0]
			basebotname = self.app.config["nick"]
			if name.startswith(basebotname):
				name = name[len(basebotname):] # truncate prefix
				if name.isdigit():
					self.botstatus.remove(int(name))
		if command == "JOINEDBATTLE" and len(args) > 1:
			name = args[1]
			battleid = int(args[0])
			basebotname = self.app.config["nick"]
			if name.startswith(basebotname):
				name = name[len(basebotname):] # truncate prefix
				if name.isdigit():
					number = int(name)
					if number in self.botstatus:
						if not battleid in self.battleswithbots:
							self.battleswithbots.append(battleid)
		if command == "LEFTBATTLE" and len(args) > 1:
			name = args[1]
			battleid = int(args[0])
			basebotname = self.app.config["nick"]
			if name.startswith(basebotname):
				name = name[len(basebotname):] # truncate prefix
				if name.isdigit():
					number = int(name)
					if number in self.botstatus:
						if battleid in self.battleswithbots:
							self.battleswithbots.remove(battleid)
	def updatestatus(self,socket):
		socket.send("MYSTATUS %i\n" % int(int(0)+int(0)*2))
	def onloggedin(self,socket):
		self.updatestatus(socket)
