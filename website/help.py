# -*- coding: utf-8 -*-
import cgi
from jinja2 import Environment, FileSystemLoader
from formalchemy import Field, types
import cgitb,helpstrings
cgitb.enable()	

def tokenizeHelp( string ):
	ret = []
	for l in string.split('\n'):
		items = l.split(':')
		if len(items) == 2:
			ret.append( (items[0], items[1] ) )
	return ret
	
env = Environment(loader=FileSystemLoader('templates'))

try:
	template = env.get_template('help.html')
	print template.render(\
		ladder_admin_commands=tokenizeHelp(helpstrings.helpstring_ladder_admin_manager),\
		global_admin_commands=tokenizeHelp(helpstrings.helpstring_global_admin_manager),\
		user_commands=tokenizeHelp(helpstrings.helpstring_user_manager),\
		battleroom_commands=tokenizeHelp(helpstrings.helpstring_user_slave) )
	
except Exception, m:
	template = env.get_template('error.html')
	print template.render( err_msg=(str(m)) )