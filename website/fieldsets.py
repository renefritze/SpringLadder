#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgi
from ladderdb import *
from db_entities import *
from formalchemy import FieldSet, Grid, ValidationError, FieldRenderer
import ParseConfig

config = ParseConfig.readconfigfile( 'Main.conf' )
db = LadderDB(config['alchemy-uri'])
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
		return '<a href="/admin/change_ladder.py?delete=%s" >delete</a>'%(value)

class Submit:
	dummy = None

Grid.default_renderers[Submit] = SubmitRenderer

class LadderInfoToTableAdapter:
	def __init__(self,ladder):
		self.ladder = ladder
		self.rows 	= []
		self.rows.append( [ 'min_ai_count' 		, ladder.min_ai_count 	] )
		self.rows.append( [ 'max_ai_count' 		, ladder.max_ai_count 	] )
		self.rows.append( [ 'min_team_size' 	, ladder.min_team_size ] )
		self.rows.append( [ 'max_team_size' 	, ladder.max_team_size ] )
		self.rows.append( [ 'min_ally_size' 	, ladder.min_ally_size ] )
		self.rows.append( [ 'max_ally_size' 	, ladder.max_ally_size ] )
		self.rows.append( [ 'min_ally_count' 	, ladder.min_ally_count ] )
		self.rows.append( [ 'max_ally_count' 	, ladder.max_ally_count ] )
		self.rows.append( [ 'min_team_count' 	, ladder.min_team_count ] )
		self.rows.append( [ 'max_team_count' 	, ladder.max_team_count ] )
		self.rows.append( [ 'ranking_algo_id' 	, ladder.ranking_algo_id ] )

class MatchInfoToTableAdapter:
	def __init__(self, match ):
		self.match = match
		self.rows = []
		self.rows.append( [ 'date'		, match.date] )
		self.rows.append( [ 'modname'	, match.modname] )
		self.rows.append( [ 'mapname'	, match.mapname] )
		self.rows.append( [ 'replay'	, match.replay ] )
		self.rows.append( [ 'duration'	, match.duration] )
