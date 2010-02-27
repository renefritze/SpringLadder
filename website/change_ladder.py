#!/usr/bin/python
# -*- coding: utf-8 -*-

from fieldsets import *
from formalchemy import Field, types
from ladderdb import ElementNotFoundException, EmptyRankingListException
from db_entities import Option

def output( db, env, request ):

	id = getSingleField( 'id', request, getSingleFieldPOST('id', request )  )
	session = db.sessionmaker()
	note = ''
	ladderFields = dict()
	optionFields = dict()

	if getSingleFieldPOST( 'submit', request  ) == 'submit':
		ladderFields = getFieldsByPrefixPOST('Ladder', request )
		optionFields = getFieldsByPrefixPOST('Option', request )
		print optionFields

	todelete = getSingleField( 'delete', request  )
	if  todelete:
		option = session.query(Option).filter(Option.ladder_id == id).filter(Option.id == int(todelete)).first()
		session.delete( option )
		session.commit()

	try:
		lad = db.GetLadder( id )
		options = session.query(Option).filter(Option.ladder_id == id).all()
		if getSingleFieldPOST( 'new', request ) == 'add new option':
			new_opt = Option()
			new_opt.ladder_id = id
			session.add( new_opt )
			session.commit()
			options.append( new_opt )
			note = 'new field'
		grid = Grid( Option, options )

		try:
			if len(ladderFields) > 0:
				fs2 = FieldSet(lad,data=ladderFields)
				if fs2.validate():
					fs2.sync()
					session.commit()
			else:
				fs2 = FieldSet(lad)
			if len(optionFields) > 0:
				grid = Grid( Option, options, data=request.POST )
				if grid.validate():
					grid.sync()
					session.commit()
			else:
				grid = Grid( Option, options )
		except ValidationError, e:
			note = '<h3> Validation failed </h3>'


		but = Field(' ', type=Submit, value=lambda item: item.id)


		grid.append(but)
		#grid.configure(include=[grid.JJ.with_renderer(SubmitRenderer)])
		gdata=grid.render()
		template = env.get_template('change_ladder.html')
		return template.render( formcontent=fs2.render(),griddata=gdata, ladder_id=id, note=note )

	except ElementNotFoundException, e:
		template = env.get_template('error.html')
		return template.render( err_msg="ladder with id %s not found"%(str(id)) )
