#!/usr/bin/python
# -*- coding: utf-8 -*-

from fieldsets import *
import forms
from ladderdb import ElementNotFoundException, EmptyRankingListException
from db_entities import Option, Roles
import bottle
from ranking import GlobalRankingAlgoSelector
from bottle import route,request
from globe import db,env
from auth import AuthDecorator

def getBodyContent( string ):
	b = string.find('<body>')
	e = string.find('</body>')
	return string[b+len('<body>')+1:e-1]

def handleAlgoChange( db, env, request, ladder ):
	try:
		new_algo = getSingleFieldPOST( 'ranking_algo_id', request )
		old_algo = ladder.ranking_algo_id
		if new_algo != old_algo:
			pre = GlobalRankingAlgoSelector.GetWebRepresentation( db.GetRanks( ladder.id ), db )
			db.SetLadderRankingAlgo( ladder.id, new_algo )
			post = GlobalRankingAlgoSelector.GetWebRepresentation( db.GetRanks( ladder.id ), db )
			return (pre,post)
	except Exception,e:
		print e
	return None
		
@route('/admin/ladder', method='POST')
@route('/admin/ladder', method='GET')
@AuthDecorator( Roles.User, db )
def output( ):

	id = getSingleField( 'id', request, getSingleFieldPOST('id', request )  )
	session = db.sessionmaker()
	user = request.player
	note = ''
	extrainfo = None
	try:
		if not db.AccessCheck( id, request.player.nick, Roles.LadderAdmin ):
			template = env.get_template('error.html')
			session.close()
			return template.render( err_msg="you're not allowed to edit ladder #%s"%(str(id)) )
		lad = db.GetLadder( id )
		session.add( lad )
		options = lad.options
		to_delete = getFieldsByPrefixPOST('delete', request )
		if to_delete and len(to_delete) > 0:
			del_key = to_delete.keys()[0]
			if to_delete[del_key] == 'delete':
				del_idx = int(del_key.split('-')[-1])
				del_opt = options[del_idx]
				session.delete( del_opt )
				session.commit()
				#redirect to same page here cause i had troubles with double session elements otherwise
				return bottle.redirect('/admin/ladder?id=%s'%id)
		if getSingleFieldPOST( 'addadmin', request  ) == 'add':
			if not db.AccessCheck( id, request.player.nick, Roles.GlobalAdmin ):
				template = env.get_template('error.html')
				session.close()
				return template.render( err_msg="you're not allowed to add an admin to ladder #%s"%(str(id)) )
			admin_name = getSingleFieldPOST( 'adminname', request, 'koko' )
			db.AddLadderAdmin( id, admin_name )
			session.close()
			return bottle.redirect('/admin/ladder?id=%s'%id)
		if getSingleFieldPOST( 'new', request  ) == 'add new option':
			opt = Option('','')
			opt.ladder_id = id
			session.add( opt )
			session.commit()
			session.add( lad )
			options = lad.options
		form = forms.Ladder(request.POST, lad, options=options )
		if getSingleFieldPOST( 'submit', request  ) == 'submit' and form.validate():
			extrainfo = handleAlgoChange( db, env, request, lad )
			form.populate_obj( lad )
			session.add( lad )
			session.commit()
			note='Ladder updated'
		#else:#enable this for debug
			#if len(form.errors) > 0:
				#note= form.errors
		textfields = []
		for var in forms.Ladder.field_order:
			textfields.append( getattr(form, var)  )
		template = env.get_template('change_ladder.html')
		session.close()
		return template.render( form=form, ladder_id=id, note=note, textfields=textfields, isglobal=user.role >= Roles.GlobalAdmin, extrainfo=extrainfo )

	except ElementNotFoundException, e:
		template = env.get_template('error.html')
		session.close()
		return template.render( err_msg=str(e) )
