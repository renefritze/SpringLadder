# -*- coding: utf-8 -*-
import cgi
from jinja2 import Environment, FileSystemLoader
from fieldsets import *
from formalchemy import Field, types
import cgitb
cgitb.enable()
env = Environment(loader=FileSystemLoader('templates'))

try:
	template = env.get_template('help.html')
	print template.render()
	
except Exception, m:
	template = env.get_template('error.html')
	print template.render( err_msg=(str(m)) )