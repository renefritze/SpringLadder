#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgi
from jinja2 import Environment, FileSystemLoader
from fieldsets import *
from formalchemy import Field, types
from sqlalchemy import func
import cgitb
cgitb.enable()
env = Environment(loader=FileSystemLoader('templates'))

player_name = getSingleField( 'player' )
order = getSingleField( 'order', 'nick' )
ladder_id = getSingleField( 'ladder' )
try:
	s = db.sessionmaker()
	if player_name:
		player = db.GetPlayer( player_name )
		template = env.get_template('viewplayer.html')
		print template.render(player=player )
	else:
		asc = bool(getSingleField( 'asc', False ))
		q = s.query( Player, func.count(Result.id).label('played')).outerjoin( (Result, Result.player_id == Player.id ) )\
			.filter( Player.id.in_(s.query( Result.player_id ).filter( Player.id == Result.player_id  ) ) ) \
			.filter( Result.player_id == Player.id ).group_by( Player.id )
		if ladder_id:
			q = q.filter( Player.id.in_( s.query( Result.player_id ).filter( Result.ladder_id == ladder_id ) ) )
		if order == 'nick':
			q = q.order_by( SortAsc( Player.nick, asc ) )
		else:
			order = 'id'
			q = q.order_by( SortAsc( Player.id, asc ) )

		limit = int(getSingleField( 'limit', q.count() ))
		offset = int(getSingleField( 'offset', 0 ))
		players = q[offset:offset+limit-1]
		template = env.get_template('viewplayerlist.html')
		print template.render(players=players,offset=offset,limit=limit,order=order )

except ElementNotFoundException, e:
	template = env.get_template('error.html')
	print template.render( err_msg="player %s not found"%(str(player_name)) )
except EmptyRankingListException, m:
	template = env.get_template('error.html')
	print template.render( err_msg=(str(m)) )