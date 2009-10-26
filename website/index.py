#!/usr/bin/python

from jinja2 import Environment, FileSystemLoader
from ladderdb import *
env = Environment(loader=FileSystemLoader('templates'))

template = env.get_template('index.html')

db = LadderDB("sqlite:///../ladder.db")

print template.render(ladders=db.GetLadderList(Ladder.name))

