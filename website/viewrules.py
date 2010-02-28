# -*- coding: utf-8 -*-

from fieldsets import LadderOptionsAdapter, LadderInfoToTableAdapter, getSingleField
from bottle import route,request
from globe import db,env

@route('/rules')
def output( ):
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