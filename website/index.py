#!/usr/bin/python
# -*- coding: utf-8 -*-
from ladderdb import *
from sqlalchemy import func
from bottle import route,request
from globe import db,env

@route('/')
def output():
	try:
		s = db.sessionmaker()
		limit = 10
		matches_header = 'Recent Matches'
		matches = s.query( Match ).order_by(Match.date.desc())[:limit]

		players_header = 'Active Players'
		player_ids = s.query( func.count( Result.player_id ), Result.player_id ).group_by( Result.player_id ).order_by( func.count(Result.player_id).desc() )[:limit]
		players = []
		for (count,pid) in player_ids:
			players.append( (s.query( Player ).filter( Player.id == pid ).one(), count ) )

		ladders_header = 'Active Ladders'
		ladder_ids = s.query( func.count( Match.ladder_id ), Match.ladder_id ).group_by( Match.ladder_id ).order_by( func.count(Match.ladder_id).desc() ).all()
		ladders = []
		for (count,lid) in ladder_ids:
			q = s.query( Ladder ).filter( Ladder.id == lid )
			if q.first():
				ladders.append( ( q.first(), count ) )


		template = env.get_template('index.html')
		ret = template.render( matches=matches, matches_header= matches_header, ladders_header=ladders_header, ladders=ladders, players_header=players_header, players=players  )
		s.close()
		return ret
		
	except Exception, m:
		if s:
			s.close()
		template = env.get_template('error.html')
		return template.render( err_msg=(str(m)) )

