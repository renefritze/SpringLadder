# -*- coding: utf-8 -*-

from fieldsets import *
import forms
from ladderdb import ElementNotFoundException, EmptyRankingListException
from db_entities import Option, Roles, Ladder
from wtforms import Form, BooleanField, TextField, validators, FieldList, \
	FormField, HiddenField, BooleanField, IntegerField, SelectField
from ranking import GlobalRankingAlgoSelector
from bottle import route,request
from globe import db,env
from auth import AuthDecorator

@route('/admin/recalc', method='GET')
@AuthDecorator( Roles.User, db )
def output( ):

	session = db.sessionmaker()
	user = request.player
	try:
		id = getSingleField( 'id', request, getSingleFieldPOST('id', request )  )
		if not db.AccessCheck( id, request.player.nick, Roles.LadderAdmin ):
			template = env.get_template('error.html')
			session.close()
			return template.render( err_msg="you're not allowed to edit ladder #%s"%(str(id)) )
		pre = GlobalRankingAlgoSelector.GetWebRepresentation( db.GetRanks( id ), db )
		db.RecalcRankings(id)
		post = GlobalRankingAlgoSelector.GetWebRepresentation( db.GetRanks( id ), db )
		lad = db.GetLadder( id )
		template = env.get_template('recalc.html')
		session.close()
		return template.render( pre=pre, post=post, ladder=lad )

	except ElementNotFoundException, e:
		err = str(e)

	except EmptyRankingListException:
		err = 'This ladder does not have any ranks to recalculate yet'

	template = env.get_template('error.html')
	session.close()
	print request.environ
	return template.render( err_msg=err )