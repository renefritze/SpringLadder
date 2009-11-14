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
	s = db.sessionmaker()
	if not id:
		template = env.get_template('viewmatchlist.html')
		matches = s.query( Match ).order_by(Match.date.desc())[:10]
		
		print template.render(matches=matches )
	else:
		ladder = db.GetLadder( id )
		template = env.get_template('viewmatch.html')
		match = s.query( Match ).filter(Match.id == id ).first()
		ladder = s.query( Ladder ).filter( Ladder.id == match.ladder_id ).first()
		opt_headers = ['key','val','wl/bl']
		print template.render(ladder=ladder, matchinfo=MatchInfoToTableAdapter(match) )

except ElementNotFoundException, e:
	template = env.get_template('error.html')
	print template.render( err_msg="ladder with id %s not found"%(str(id)) )
except EmptyRankingListException, m:
	template = env.get_template('error.html')
	print template.render( err_msg=(str(m)) )