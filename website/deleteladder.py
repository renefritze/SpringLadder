# -*- coding: utf-8 -*-
from fieldsets import *
import forms
from ladderdb import ElementNotFoundException, EmptyRankingListException
from db_entities import Option, Roles, Ladder
from wtforms import Form, BooleanField, TextField, validators, FieldList, \
	FormField, HiddenField, BooleanField, IntegerField, SelectField
from ranking import GlobalRankingAlgoSelector

def output( db, env, request ):

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
	return template.render( err_msg=str(e) )