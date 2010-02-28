# -*- coding: utf-8 -*-
import helpstrings
from bottle import route,request
from globe import db,env,cache

def tokenizeHelp( string ):
	ret = []
	for l in string.split('\n'):
		items = l.split(':')
		if len(items) == 2:
			ret.append( (items[0], items[1] ) )
	return ret

@cache.cache('help_output', expire=3600)
@route('/help')
def output( ):
	try:
		template = env.get_template('help.html')
		return template.render(\
			ladder_admin_commands=tokenizeHelp(helpstrings.helpstring_ladder_admin_manager),\
			global_admin_commands=tokenizeHelp(helpstrings.helpstring_global_admin_manager),\
			user_commands=tokenizeHelp(helpstrings.helpstring_user_manager),\
			battleroom_commands=tokenizeHelp(helpstrings.helpstring_user_slave) )

	except Exception, m:
		template = env.get_template('error.html')
		return template.render( err_msg=(str(m)) )