#!/usr/bin/python
# -*- coding: utf-8 -*-

from jinja2 import Environment, FileSystemLoader
from ladderdb import *
from fieldsets import db
env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('index.html')
print template.render(ladders=db.GetLadderList(Ladder.name) )

