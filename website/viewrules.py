# -*- coding: utf-8 -*-
import cgi
from jinja2 import Environment, FileSystemLoader
from fieldsets import *
from formalchemy import Field, types
import cgitb
cgitb.enable()
env = Environment(loader=FileSystemLoader('templates'))

id = getSingleField( 'id' )

try:
	ladder = db.GetLadder( id )
	template = env.get_template('viewrules.html')
	options = db.GetOptions( id )
	opt_headers = ['key','val','wl/bl']
	print template.render(ladder=ladder, laddertable=LadderInfoToTableAdapter(ladder), options=options, opt_headers=opt_headers)

except ElementNotFoundException, e:
	template = env.get_template('error.html')
	print template.render( err_msg="ladder with id %s not found"%(str(id)) )
except EmptyRankingListException, m:
	template = env.get_template('error.html')
	print template.render( err_msg=(str(m)) )