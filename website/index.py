#!/usr/bin/python

from jinja2 import Environment, FileSystemLoader
from ladderdb import *
import formhelper
env = Environment(loader=FileSystemLoader('templates'))

template = env.get_template('index.html')

db = LadderDB("sqlite:///../ladder.db")

field = formhelper.getValue("dummy")

print template.render(ladders=db.GetLadderList(Ladder.name), param=field )

