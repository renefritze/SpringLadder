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
		ladders = db.GetLadderByPlayer( player.id )
		played = dict()
		positions = dict()
		for ladder in ladders:
			positions[ladder.id] = db.GetPlayerPostion( ladder.id, player.id )
			played[ladder.id] = s.query( Result.id ).filter( Result.ladder_id == ladder.id ).filter( Result.player_id == player.id ).count()

		results = s.query( Result ).filter( Result.player_id == player.id).order_by(Result.date.desc())[0:5]
		matches = []
		for r in results:
			matches.append( r.match )

		template = env.get_template('viewplayer.html')
		print template.render(player=player,ladders=ladders, positions=positions,played=played,matches=matches )
	else:
		asc = getSingleField( 'asc', 'False' )
		if not asc:
			asc = 'False'
		q = s.query( Player, func.count(Result.id).label('played')).outerjoin( (Result, Result.player_id == Player.id ) )\
			.filter( Player.id.in_(s.query( Result.player_id ).filter( Player.id == Result.player_id  ) ) ) \
			.filter( Result.player_id == Player.id ).group_by( Player.id )
		if ladder_id:
			q = q.filter( Player.id.in_( s.query( Result.player_id ).filter( Result.ladder_id == ladder_id ) ) )
		if order == 'nick':
			q = q.order_by( SortAsc( Player.nick, asc ) )
		elif order == 'id' :
			q = q.order_by( SortAsc( Player.id, asc ) )
		else:
			order = 'played'
			q = q.order_by( SortAsc( func.count(Result.id), asc ) )

		limit = int(getSingleField( 'limit', q.count() ))
		offset = int(getSingleField( 'offset', 0 ))
		players = q[offset:offset+limit-1]
		template = env.get_template('viewplayerlist.html')
		print template.render(players=players,offset=offset,limit=limit,order=order,asc=asc )

except ElementNotFoundException, e:
	template = env.get_template('error.html')
	print template.render( err_msg="player %s not found"%(str(player_name)) )
except EmptyRankingListException, m:
	template = env.get_template('error.html')
	print template.render( err_msg=(str(m)) )