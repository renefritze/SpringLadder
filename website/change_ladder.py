#!/usr/bin/python
# -*- coding: utf-8 -*-

from fieldsets import *
import forms
from ladderdb import ElementNotFoundException, EmptyRankingListException
from db_entities import Option
from wtforms import Form, BooleanField, TextField, validators, FieldList, \
	FormField, HiddenField, BooleanField, IntegerField, SelectField


def output( db, env, request ):

	id = getSingleField( 'id', request, getSingleFieldPOST('id', request )  )
	session = db.sessionmaker()
	note = ''
	ladderFields = dict()
	optionFields = dict()

	#if getSingleFieldPOST( 'submit', request  ) == 'submit':
		#ladderFields = getFieldsByPrefixPOST('Ladder', request )
		#optionFields = getFieldsByPrefixPOST('Option', request )
		#print optionFields

	#todelete = getSingleField( 'delete', request  )
	#if  todelete:
		#option = session.query(Option).filter(Option.ladder_id == id).filter(Option.id == int(todelete)).first()
		#session.delete( option )
		#session.commit()

	try:
		lad = db.GetLadder( id )
		session.add( lad )
		options = lad.options
		if getSingleFieldPOST( 'new', request  ) == 'add new option':
			opt = Option('','')
			opt.ladder_id = id
			session.add( opt )
			session.commit()
			session.add( lad )
			options = lad.options
		form = forms.Ladder(request.POST, lad, options=options )
		if getSingleFieldPOST( 'submit', request  ) == 'submit' and form.validate():
			form.populate_obj( lad )
			session.add( lad )
			session.commit()
			note='Ladder updated'
		textfields = []
		for var in forms.Ladder.field_order:
			textfields.append( getattr(form, var)  )
		template = env.get_template('change_ladder.html')
		
		return template.render( form=form, ladder_id=id, note=note, textfields=textfields )

	except ElementNotFoundException, e:
		template = env.get_template('error.html')
		return template.render( err_msg="ladder with id %s not found"%(str(id)) )
