# -*- coding: utf-8 -*-
from fieldsets import *
from db_entities import Player, Result, Ladder
from bottle import route,request
from globe import db,env,cache

@route('/fame')
@cache.cache('fame_output', expire=600)
def output(  ):
	try:
		limit = 10
		template = env.get_template('fame.html')
		s = db.sessionmaker()
		player_ids = s.query( Result.player_id ).group_by( Result.player_id )
		ladder_playerpos = dict()
		playerpos = []
		for pid in player_ids:
			pid = pid[0]
			ladders = s.query( Ladder ).filter( Ladder.id.in_( s.query( Result.ladder_id ).filter( Result.player_id == pid ).group_by( Result.ladder_id ) ) )
			score = 0
			l_names = []
			for l in ladders:
				player_per_ladder = s.query( Result.player_id ).filter( Result.ladder_id == l.id ).group_by( Result.player_id ).count()
				pos = db.GetPlayerPosition( l.id, pid )
				score += ( 1 - ( pos / float( player_per_ladder ) ) ) * 1000
				l_names.append( '%s (%d)'%(l.name,pos) )
			if ladders.count() > 0:
				playername = s.query( Player.nick ).filter( Player.id == pid ).first()[0]
				playerpos.append( (playername, int(score), ', '.join(l_names) ) )

		playerpos.sort( lambda x, y: cmp(y[1], x[1]) )
		header = ['Name', 'Score', 'Active on (position on ladder)' ]

		leaders = []
		losers = []
		for name, id in s.query( Ladder.name, Ladder.id ):
			try:
				r = db.GetRanks( id )
				if len(r) > 1:
					s.add( r[0] )
					s.add( r[-1] )
					leaders.append( (r[0].player.nick, name, r[-1].player.nick  ) )
			except ElementNotFoundException:
				continue #empty ladder
		losers.sort( lambda x, y: cmp(x[1], y[1]) )
		leaders.sort( lambda x, y: cmp(x[1], y[1]) )
		s.close()
		return template.render( playerpos_top=playerpos[0:limit],playerpos_bottom=playerpos[-limit:], header=header, leaders=leaders,losers=losers )

	except Exception, m:
		if s:
			s.close()
		template = env.get_template('error.html')
		return template.render( err_msg=(str(m)) )