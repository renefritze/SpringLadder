#!/usr/bin/python

import cgi
from fieldsets import db,fs,session,ladders
import cgitb
cgitb.enable()

lad = ladders
fields = cgi.FieldStorage()
f2 = dict()
for k in fields.keys():
	f2[k] = fields.getvalue(k)
fields = f2
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

html = fs2.render()
h = '<form name="input" action="enter.py" method="post">'
f = '<input type="submit" value="Submit" /></form>'
print h,html,f
