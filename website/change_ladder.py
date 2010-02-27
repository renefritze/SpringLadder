#!/usr/bin/python
# -*- coding: utf-8 -*-

from fieldsets import *
import forms
from ladderdb import ElementNotFoundException, EmptyRankingListException
from db_entities import Option
from wtforms import Form, BooleanField, TextField, validators, FieldList, FormField, HiddenField

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
		options = session.query(Option).filter(Option.ladder_id == id).all()
		form = forms.Ladder(request.POST, lad, options=options )
		if getSingleFieldPOST( 'submit', request  ) == 'submit' and form.validate():
			lad.name 		= form.name.data
			lad.description = form.description.data
			session.add( lad )
			session.commit()
			note='added'
		if form.errors:
			print form.errors
		textfields = []
		for var in vars(form).keys():
			#print var
			attr = getattr(form, var) 
			if isinstance( attr, TextField ):
				textfields.append( attr )
		template = env.get_template('change_ladder.html')
		return template.render( form=form, ladder_id=id, note=note, textfields=textfields )

	except ElementNotFoundException, e:
		template = env.get_template('error.html')
		return template.render( err_msg="ladder with id %s not found"%(str(id)) )
