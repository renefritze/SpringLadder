#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgi
from jinja2 import Environment, FileSystemLoader
from fieldsets import *
import cgitb
cgitb.enable()
env = Environment(loader=FileSystemLoader('templates'))

fields = cgi.FieldStorage()
f2 = dict()
for k in fields.keys():
	f2[k] = fields.getvalue(k)
fields = f2

id = 1
if 'id' in f2:
	id = f2['id']
	del f2['id']

fs2 = None

try:
	lad = db.GetLadder( id )
	options = session.query(Option).filter(Option.ladder_id == id).all()
	grid = Grid( Option, options )
#print fields
	if fields:
		fs2 = FieldSet(lad,data=f2)
		try:
			fs2.validate()
			fs2.sync()
			session.commit()
			print '<h3> done </h3>'
		except:
			print '<h3> failed </h3>'

	else:
		fs2 = FieldSet(lad)
		grid = Grid( Option, options )

	template = env.get_template('change_ladder.html')
	print template.render( formcontent=fs2.render(),griddata=grid.render() )

except ElementNotFoundException, e:
	template = env.get_template('error.html')
	print template.render( err_msg="ladder with id %s not found"%(str(id)) )