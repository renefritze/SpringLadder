#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgi
from fieldsets import db,fs,session,ladders
from fa.jquery.forms import *
from jinja2 import Environment, FileSystemLoader
import cgitb
cgitb.enable()

env = Environment(loader=FileSystemLoader('templates'))
fs2 = fs.bind(ladders[0])
fs3 = fs.bind(ladders[1])

tabs = Tabs('my_tabs', ('tab1', 'My first tab', fs2) )
tabs.append('tab2', 'The second', fs3)
tabs.tab1 = tabs.tab1.bind(ladders[0])
tabs.bind(ladders[1], tabs.tab2)

template = env.get_template('tabs.html')
print template.render( formcontent=tabs.render(selected=2) )
