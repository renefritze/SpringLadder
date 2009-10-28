#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgi
from ladderdb import *
from db_entities import *
from formalchemy import FieldSet, Grid
db = LadderDB("sqlite:///../ladder.db")
session = db.getSession()


