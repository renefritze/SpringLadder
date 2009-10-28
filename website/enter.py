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

from fa.jquery.forms import *
tabs = Tabs('my_tabs',
	('tab1', 'My first tab', fs2),
	footer='<input type="submit" action="enter.py" method="post" name="%(id)s" />')

tabs.append('tab2', 'The second', fs2)
tabs.tab1 = tabs.tab1.bind(lad)
tabs.bind(lad, tabs.tab2)
h = '''<html>
<head>
<link type="text/css" href="/jquery/css/redmond/jquery-ui-1.7.2.custom.css" rel="stylesheet" />
<link type="text/css" href="/jquery/fa.jquery.min.css" rel="stylesheet" />
<script type="text/javascript" src="/jquery/fa.jquery.min.js"></script>
</head>
<form name="input" action="enter.py" method="post">'''
f ='''</html>
''' 

#<input type="submit" value="Submit" /></form>'
print h,tabs.render(selected=2),f

