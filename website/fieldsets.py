#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgi
from ladderdb import *
from db_entities import *
from formalchemy import FieldSet, Grid, ValidationError, FieldRenderer
db = LadderDB("sqlite:///../ladder.db")
session = db.getSession()

fields = cgi.FieldStorage()

def getFieldsByPrefix( prefix ):
	global fields
	filtered = dict()
	for k in fields.keys():
		if k.startswith( prefix ):
			filtered[k] = fields.getvalue(k)
	return filtered

def getAllFields( prefix ):
	global fields
	filtered = dict()
	for k in fields.keys():
		filtered[k] = fields.getvalue(k)
	return filtered

def getSingleField( key ):
	global fields
	if key in fields.keys():
		return fields.getvalue(key)
	else:
		return None

class SubmitRenderer(FieldRenderer):
	def render(self):
		value= self._value and self._value or ''
		#return '<input name="delete" type="submit" value="%s" title="delete"/>'%(value)
		return '<a href="/change_ladder.py?delete=%s" >delete</a>'%(value)

class Submit:
	dummy = None

Grid.default_renderers[Submit] = SubmitRenderer


