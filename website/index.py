#!/usr/bin/python
# -*- coding: utf-8 -*-

from jinja2 import Environment, FileSystemLoader
from ladderdb import *
from fieldsets import db

env = Environment(loader=FileSystemLoader('templates'))

try:
	s = db.sessionmaker()
	limit = 10
	matches = s.query( Match ).order_by(Match.date.desc())[:limit]
	matches_header = 'Recent Matches'
	players_header = 'Active Players'
	players = []
	ladders_header = 'Active Ladders'
	ladders = []
	template = env.get_template('index.html')
	print template.render( matches=matches, matches_header= matches_header, ladders_header=ladders_header, ladders=ladders, players_header=players_header, players=players  )

except Exception, m:
	template = env.get_template('error.html')
	print template.render( err_msg=(str(m)) )

