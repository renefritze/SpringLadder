#!/usr/bin/python
# -*- coding: utf-8 -*-
from formalchemy import Field, types
from ladderdb import *
from fieldsets import getSingleField, MatchInfoToTableAdapter
from bottle import route,request
from globe import db,env

@route('/match')
def output( ):
	id = getSingleField( 'id', request )
	player_name = getSingleField( 'player', request )
	ladder_id = getSingleField( 'ladder', request )
	limit = getSingleField( 'limit', request, 18 )
	ret = ''
	try:
		s = db.sessionmaker()
		if player_name and ladder_id:
			ladder = db.GetLadder( ladder_id )
			player = db.GetPlayer( player_name )
			template = env.get_template('viewmatchlist.html')
			header_string = 'Matches for %s on ladder %s'%(player.nick,ladder.name)
			matches = s.query( Match ).filter(Match.ladder_id == ladder_id).order_by(Match.date.desc()).all()
			ret = template.render(matches=matches, header=header_string )
		elif ladder_id:
			ladder = db.GetLadder( ladder_id )
			header_string = 'Matches on ladder %s'%(ladder.name)
			template = env.get_template('viewmatchlist.html')
			matches = s.query( Match ).filter(Match.ladder_id == ladder_id).order_by(Match.date.desc()).all()
			ret = template.render(matches=matches, header=header_string )
		elif player_name:
			player = db.GetPlayer( player_name )
			template = env.get_template('viewmatchlist.html')
			header_string = 'Matches for %s'%(player.nick)
			results = s.query( Result ).filter( Result.player_id == player.id).order_by(Result.date.desc())
			matches = []
			for r in results:
				matches.append( r.match )
			ret = template.render(matches=matches, header=header_string )
		elif not id:
			template = env.get_template('viewmatchgrid.html')
			matches = s.query( Match ).order_by(Match.date.desc())[:limit]
			ret = template.render( matches=matches, limit=limit )
		else:
			match = s.query( Match ).options(eagerload('settings')).filter(Match.id == id ).first()
			template = env.get_template('viewmatch.html')
			opt_headers = ['key','val','wl/bl']
			ret = template.render(ladder=match.ladder, matchinfo=MatchInfoToTableAdapter(match) )
		s.close()
		return ret
		
	except ElementNotFoundException, e:
		err_msg="ladder with id %s not found"%(str(id))

	except EmptyRankingListException, m:
		err_msg=(str(m))

	if s:
		s.close()
	template = env.get_template('error.html')
	return template.render( err_msg=err_msg )