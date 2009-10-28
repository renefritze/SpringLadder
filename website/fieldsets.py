#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgi
from ladderdb import *
from db_entities import *
from formalchemy import FieldSet
db = LadderDB("sqlite:///../ladder.db")
session = db.getSession()
ladders = session.query(Ladder).all()
fs = FieldSet(ladders[0],session)

