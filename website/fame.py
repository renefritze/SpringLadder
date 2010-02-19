# -*- coding: utf-8 -*-
import cgi
from jinja2 import Environment, FileSystemLoader
from fieldsets import *
from formalchemy import Field, types
import cgitb
cgitb.enable()
env = Environment(loader=FileSystemLoader('templates'))

try:
	template = env.get_template('fame.html')
	s = db.sessionmaker()
	player_ids = s.query( Result.player_id ).group_by( Result.player_id )
	ladder_playerpos = dict()
	playerpos = []
	for pid in player_ids:
		pid = pid[0]
		ladders = s.query( Ladder ).filter( Ladder.id.in_( s.query( Result.ladder_id ).filter( Result.player_id == pid ).group_by( Result.ladder_id ) ) )
		score = 0
		for l in ladders:
			player_per_ladder = s.query( Result.player_id ).filter( Result.ladder_id == l.id ).group_by( Result.player_id ).count()
			pos = db.GetPlayerPosition( l.id, pid )
			score += ( 1 - ( pos / float( player_per_ladder ) ) ) * float( player_per_ladder )
		if ladders.count() > 0:
			#score /= float( ladders.count() )
			playername = s.query( Player.nick ).filter( Player.id == pid ).first()[0]
			playerpos.append( (playername, score ) )

	playerpos.sort( lambda x, y: cmp(y[1], x[1]) )
	header = ['Name', 'Score' ]
	print template.render( playerpos=playerpos[0:10], header=header )
	
except Exception, m:
	template = env.get_template('error.html')
	print template.render( err_msg=(str(m)) )