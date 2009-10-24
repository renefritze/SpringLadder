from colors import *
from ParseConfig import *
class Main:
	sock = 0
	def onload(self,tasc):
		pass
	def oncommandfromserver(self,command,args,socket):
		pass
	def onloggedin(self,socket):
		for channel in self.app.config["channelautojoinlist"]:
			socket.send("JOIN " + channel + "\n")		
