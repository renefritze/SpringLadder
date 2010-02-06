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
try:
	if not id:
		template = env.get_template('viewladderlist.html')
		print template.render(ladders=db.GetLadderList(Ladder.name) )
	else:
		ladder = db.GetLadder( id )
		template = env.get_template('viewladder.html')
		ranks = db.GetRanks( id, None, 10 )
		rank_table = GlobalRankingAlgoSelector.GetWebRepresentation( ranks, db )
		print template.render(ladder=ladder, rank_table=rank_table )

except ElementNotFoundException, e:
	template = env.get_template('error.html')
	print template.render( err_msg="ladder with id %s not found"%(str(id)) )
except EmptyRankingListException, m:
	template = env.get_template('error.html')
	print template.render( err_msg=(str(m)) )