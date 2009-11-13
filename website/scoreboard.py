#!/usr/bin/python
# -*- coding: utf-8 -*-
import cgi
from jinja2 import Environment, FileSystemLoader
from fieldsets import *
from formalchemy import Field, types
import cgitb
cgitb.enable()
env = Environment(loader=FileSystemLoader('templates'))

id = getSingleField( 'id' )
if not id :
	id = 1

note = ''

try:
	lad = db.GetLadder( id )
	ranks = db.GetRanks( id )
	
	rank_table = GlobalRankingAlgoSelector.GetWebRepresentation( db.GetRanks( id ), db )
	template = env.get_template('scoreboard.html')
	print template.render( rank_table=rank_table, ladder_id=id  )

except ElementNotFoundException, e:
	template = env.get_template('error.html')
	print template.render( err_msg="ladder with id %s not found"%(str(id)) )
