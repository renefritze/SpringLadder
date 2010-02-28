# -*- coding: utf-8 -*-

from fieldsets import *
import forms
from ladderdb import ElementNotFoundException, EmptyRankingListException
from db_entities import Option, Roles, Ladder
from wtforms import Form, BooleanField, TextField, validators, FieldList, \
	FormField, HiddenField, BooleanField, IntegerField, SelectField
import bottle

def output( db, env, request ):

	session = db.sessionmaker()
	user = request.player
	try:
		if user.role < Roles.GlobalAdmin:
			ladder_ids = session.query( Option.ladder_id ).filter( Option.key == Option.adminkey ) \
				.filter( Option.value == user.nick ).group_by( Option.ladder_id )
		else:
			ladder_ids = session.query( Ladder.id )
		ladders = session.query( Ladder ).filter( Ladder.id.in_ ( ladder_ids ) ).all()
		template = env.get_template('adminindex.html')
		session.close()
		return template.render( ladders=ladders, isglobal=user.role >= Roles.GlobalAdmin )

	except ElementNotFoundException, e:
		template = env.get_template('error.html')
		session.close()
		return template.render( err_msg=str(e) )
