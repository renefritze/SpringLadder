#!/usr/bin/python
# -*- coding: utf-8 -*-

from fieldsets import getSingleField, SortAsc
from sqlalchemy import func
from ladderdb import ElementNotFoundException, EmptyRankingListException
from db_entities import Player, Result
from bottle import route,request
from globe import db,env

@route('/player')
def output( ):
	player_name = getSingleField( 'player', request )
	order = getSingleField( 'order', request , 'nick')
	ladder_id = getSingleField( 'ladder', request )
	try:
		s = db.sessionmaker()
		if player_name:
			player = db.GetPlayer( player_name )
			ladders = db.GetLadderByPlayer( player.id )
			played = dict()
			positions = dict()
			for ladder in ladders:
				positions[ladder.id] = db.GetPlayerPosition( ladder.id, player.id )
				played[ladder.id] = s.query( Result.id ).filter( Result.ladder_id == ladder.id ).filter( Result.player_id == player.id ).count()

			results = s.query( Result ).filter( Result.player_id == player.id).order_by(Result.date.desc())[0:5]
			matches = []
			for r in results:
				matches.append( r.match )

			template = env.get_template('viewplayer.html')
			s.close()
			return template.render(player=player,ladders=ladders, positions=positions,played=played,matches=matches )
		else:
			asc = getSingleField( 'asc', request, 'False' )
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

			limit = int(getSingleField( 'limit', request, q.count() ))
			offset = int(getSingleField( 'offset', request, 0 ))
			players = q[offset:offset+limit-1]
			template = env.get_template('viewplayerlist.html')
			s.close()
			return template.render(players=players,offset=offset,limit=limit,order=order,asc=asc )

	except ElementNotFoundException, e:
		err_msg="player %s not found"%(str(player_name))

	except EmptyRankingListException, m:
		err_msg=(str(m))
	if s:
		s.close()
	template = env.get_template('error.html')
	return template.render( err_msg=err_msg )