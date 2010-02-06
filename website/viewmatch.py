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
player_name = getSingleField( 'player' )
ladder_id = getSingleField( 'ladder' )
try:
	s = db.sessionmaker()
	if player_name and ladder_id:
		ladder = db.GetLadder( ladder_id )
		player = db.GetPlayer( player_name )
		template = env.get_template('viewmatchlist.html')
		header_string = 'Matches for %s on ladder %s'%(player.nick,ladder.name)
		matches = s.query( Match ).filter(Match.ladder_id == ladder_id).order_by(Match.date.desc()).all()
		print template.render(matches=matches, header=header_string )
	elif ladder_id:
		ladder = db.GetLadder( ladder_id )
		header_string = 'Matches on ladder %s'%(ladder.name)
		template = env.get_template('viewmatchlist.html')
		matches = s.query( Match ).filter(Match.ladder_id == ladder_id).order_by(Match.date.desc()).all()
		print template.render(matches=matches, header=header_string )
	elif not id:
		template = env.get_template('viewmatchlist.html')
		limit = int(getSingleField( 'limit', 10 ))
		matches = s.query( Match ).order_by(Match.date.desc())[:limit]
		header_string = 'last %i matches'%limit
		print template.render(matches=matches, header=header_string )
	else:
		match = s.query( Match ).filter(Match.id == id ).first()
		ladder = db.GetLadder( match.ladder_id )
		template = env.get_template('viewmatch.html')
		
		ladder = s.query( Ladder ).filter( Ladder.id == match.ladder_id ).first()
		opt_headers = ['key','val','wl/bl']
		print template.render(ladder=ladder, matchinfo=MatchInfoToTableAdapter(match) )

except ElementNotFoundException, e:
	template = env.get_template('error.html')
	print template.render( err_msg="ladder with id %s not found"%(str(id)) )
except EmptyRankingListException, m:
	template = env.get_template('error.html')
	print template.render( err_msg=(str(m)) )