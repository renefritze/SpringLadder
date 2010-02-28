#!/usr/bin/python
# -*- coding: utf-8 -*-

from fieldsets import getSingleField
from ranking import GlobalRankingAlgoSelector

def output( db, env, request ):
	try:
		id = getSingleField( 'id', request )
		lad = db.GetLadder( id )
		rank_table = GlobalRankingAlgoSelector.GetWebRepresentation( db.GetRanks( id ), db )
		template = env.get_template('scoreboard.html')
		return template.render( rank_table=rank_table, ladder=lad )

	except ElementNotFoundException, e:
		err_msg="ladder with id %s not found"%(str(id))

	except EmptyRankingListException, m:
		err_msg=(str(m))
		
	template = env.get_template('error.html')
	return template.render( err_msg=err_msg )
