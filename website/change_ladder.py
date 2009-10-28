#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgi
from jinja2 import Environment, FileSystemLoader
from fieldsets import db,fs,session,ladders
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

try:
	lad = db.GetLadder( id )
	
#print fields
	if fields:
		fs2 = fs.bind(lad,data=f2)
		try:
			fs2.validate()
			fs2.sync()
			session.commit()
			print '<h3> done </h3>'
		except:
			print '<h3> failed </h3>'

	else:
		fs2 = fs.bind(lad)

	template = env.get_template('change_ladder.html')
	print template.render( formcontent=fs2.render() )

except:
	template = env.get_template('error.html')
	print template.render( err_msg="ladder with id %s not found"%(str(id)) )


