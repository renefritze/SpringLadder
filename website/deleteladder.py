# -*- coding: utf-8 -*-
from fieldsets import *
from ladderdb import ElementNotFoundException, EmptyRankingListException
from db_entities import Roles
from bottle import route,request
from globe import db,env
from auth import AuthDecorator

@route('/admin/deleteladder', method='GET')
@AuthDecorator( Roles.User, db )
def output( ):

	user = request.player
	try:
		id = getSingleField( 'id', request, getSingleFieldPOST('id', request )  )
		lad = db.GetLadder( id )
		if not db.AccessCheck( id, request.player.nick, Roles.GlobalAdmin ):
			template = env.get_template('error.html')
			return template.render( err_msg="you're not allowed to delete ladder #%s"%(str(id)) )
		ask = True
		if getSingleField( 'confirm', request  ) == 'yes':
			session = db.sessionmaker()
			session.delete( lad )
			session.commit()
			session.close()
			ask = False
		template = env.get_template('deleteladder.html')
		return template.render( ladder=lad, ask=ask )

	except ElementNotFoundException, e:
		err = str(e)

	except Exception, f:
		err = str(f)

	template = env.get_template('error.html')
	return template.render( err_msg=err )