# -*- coding: utf-8 -*-
from fieldsets import *
from ladderdb import ElementNotFoundException, EmptyRankingListException
from db_entities import Option, Match, Ladder, Roles
from bottle import route,request
from globe import db,env
from auth import AuthDecorator

@route('/admin/match', method='GET')
@AuthDecorator( Roles.User, db )
def output( ):

	user = request.player
	try:
		session = db.sessionmaker()
		id = getSingleField( 'id', request )
		mid = getSingleField( 'mid', request )
		if mid:
			if not db.AccessCheck( id, request.player.nick, Roles.LadderAdmin ):
				template = env.get_template('error.html')
				return template.render( err_msg="you're not allowed to delete match #%s"%(str(mid)) )
			lid = getSingleField( 'lid', request )
			db.DeleteMatch( lid, mid )
		if id:
			if db.AccessCheck( id, user.nick, Roles.LadderAdmin ):
				ladder_ids = [id]
			else:
				ladder_ids = []
		else:
			if user.role < Roles.GlobalAdmin:
				ladder_ids = session.query( Option.ladder_id ).filter( Option.key == Option.adminkey ) \
					.filter( Option.value == user.nick ).group_by( Option.ladder_id )
			else:
				ladder_ids = session.query( Ladder.id )
			
		matches = session.query( Match ).filter( Match.ladder_id.in_ ( ladder_ids ) )\
					.order_by( Match.ladder_id ).order_by( Match.date.desc() ).all()
		template = env.get_template('adminmatch.html')
		return template.render( matches=matches, lid=id )

	except ElementNotFoundException, e:
		err = str(e)

	except Exception, f:
		err = str(f)

	template = env.get_template('error.html')
	return template.render( err_msg=err )