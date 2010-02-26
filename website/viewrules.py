# -*- coding: utf-8 -*-

from fieldsets import LadderOptionsAdapter, LadderInfoToTableAdapter, getSingleField

def output( db, env, request ):
	id = getSingleField( 'id', request )

	try:
		ladder = db.GetLadder( id )
		template = env.get_template('viewrules.html')
		opts = db.GetOptions( id )
		options = LadderOptionsAdapter( opts , ladder )
		return template.render(ladder=ladder, laddertable=LadderInfoToTableAdapter(ladder), options=options )

	except ElementNotFoundException, e:
		template = env.get_template('error.html')
		return template.render( err_msg="ladder with id %s not found"%(str(id)) )
	except EmptyRankingListException, m:
		template = env.get_template('error.html')
		return template.render( err_msg=(str(m)) )