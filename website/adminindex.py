# -*- coding: utf-8 -*-

from fieldsets import *
import forms
from ladderdb import ElementNotFoundException, EmptyRankingListException
from db_entities import Option, Roles, Ladder
from wtforms import Form, BooleanField, TextField, validators, FieldList, \
	FormField, HiddenField, BooleanField, IntegerField, SelectField
import bottle
from bottle import route,request
from globe import db,env
from auth import AuthDecorator

@route('/admin', method='GET')
@route('/admin', method='POST')
@AuthDecorator( Roles.User, db )
def output( ):

	session = db.sessionmaker()
	user = request.player
	try:
		if getSingleFieldPOST( 'addladder', request  ) == 'add':
			if user.role >= Roles.GlobalAdmin:
				name = getSingleFieldPOST( 'laddername', request )
				if name and len(name) > 0 and len(name) <= 100:
					ladderid = db.AddLadder( name )
					session.close()
					return bottle.redirect( '/admin/ladder?id=%d'%ladderid )
				else:
					template = env.get_template('error.html')
					session.close()
					return template.render( err_msg="you're not allowed to add a ladder" )
			else:
				template = env.get_template('error.html')
				session.close()
				return template.render( err_msg="you're not allowed to add a ladder" )
		if user.role < Roles.GlobalAdmin:
			ladder_ids = session.query( Option.ladder_id ).filter( Option.key == Option.adminkey ) \
				.filter( Option.value == user.nick ).group_by( Option.ladder_id )
		else:
			ladder_ids = session.query( Ladder.id )
		ladders = session.query( Ladder ).filter( Ladder.id.in_ ( ladder_ids ) ).all()
		template = env.get_template('adminindex.html')
		session.close()
		if len(ladders) < 1:
			#no admin whatsoever
			return bottle.redirect( '/' )
		return template.render( ladders=ladders, isglobal=user.role >= Roles.GlobalAdmin )

	except ElementNotFoundException, e:
		template = env.get_template('error.html')
		session.close()
		return template.render( err_msg=str(e) )
