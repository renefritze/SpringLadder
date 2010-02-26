#!/usr/bin/python
# -*- coding: utf-8 -*-

from fieldsets import getSingleField
from ranking import GlobalRankingAlgoSelector

def output( db, env, request ):
	id = getSingleField( 'id', request )
	try:
		lad = db.GetLadder( id )

		rank_table = GlobalRankingAlgoSelector.GetWebRepresentation( db.GetRanks( id ), db )
		template = env.get_template('scoreboard.html')
		return template.render( rank_table=rank_table, ladder=lad )

	except ElementNotFoundException, e:
		template = env.get_template('error.html')
		return template.render( err_msg="ladder with id %s not found"%(str(id)) )
	except EmptyRankingListException, m:
		template = env.get_template('error.html')
		return template.render( err_msg=(str(m)) )
