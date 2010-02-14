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
	elif player_name:
		player = db.GetPlayer( player_name )
		template = env.get_template('viewmatchlist.html')
		header_string = 'Matches for %s'%(player.nick)
		results = s.query( Result ).filter( Result.player_id == player.id).order_by(Result.date.desc())
		matches = []
		for r in results:
			matches.append( r.match )
		print template.render(matches=matches, header=header_string )
	elif not id:
		template = env.get_template('viewmatchgrid.html')
		limit = int(getSingleField( 'limit', 18 ))
		matches = s.query( Match ).order_by(Match.date.desc())[:limit]
		print template.render( matches=matches, limit=limit )
	else:
		match = s.query( Match ).options(eagerload('settings')).filter(Match.id == id ).first()
		template = env.get_template('viewmatch.html')
		opt_headers = ['key','val','wl/bl']
		print template.render(ladder=match.ladder, matchinfo=MatchInfoToTableAdapter(match) )

except ElementNotFoundException, e:
	template = env.get_template('error.html')
	print template.render( err_msg="ladder with id %s not found"%(str(id)) )
except EmptyRankingListException, m:
	template = env.get_template('error.html')
	print template.render( err_msg=(str(m)) )