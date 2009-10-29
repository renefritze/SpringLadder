#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgitb
cgitb.enable()
import cgi
from fieldsets import *
from fa.jquery.forms import *
from jinja2 import Environment, FileSystemLoader

ladders = session.query(Ladder).all()
env = Environment(loader=FileSystemLoader('templates'))
fs2 = FieldSet(ladders[0])
fs3 = FieldSet(ladders[1])

tabs = Tabs('my_tabs', ('tab1', 'My first tab', fs2) )
tabs.append('tab2', 'The second', fs3)
tabs.tab1 = tabs.tab1.bind(ladders[0])
tabs.bind(ladders[1], tabs.tab2)

template = env.get_template('tabs.html')
print template.render( formcontent=tabs.render(selected=2) )
