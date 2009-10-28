#!/usr/bin/python

import cgi
from ladderdb import *
from db_entities import *
from formalchemy import FieldSet
db = LadderDB("sqlite:///../ladder.db")
session = db.getSession()
ladders = session.query(Ladder).first()
fs = FieldSet(ladders,session)

