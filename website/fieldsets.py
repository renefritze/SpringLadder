#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgi,ParseConfig
from ladderdb import *
from db_entities import *
from formalchemy import FieldSet, Grid, ValidationError, FieldRenderer
from customlog import Log

config = ParseConfig.readconfigfile( 'Main.conf' )
Log.Init( 'website.log', 'website.log' )
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

def getSingleField( key, default=None ):
	global fields
	if key in fields.keys():
		return fields.getvalue(key)
	else:
		return default

def SortAsc( condition, ascending = 'True' ):
	if ascending == 'True':
		return condition.asc()
	else:
		return condition.desc()

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
		self.rows.append( [ 'min amount of AIs' 		, ladder.min_ai_count 	] )
		self.rows.append( [ 'max amount of AIs' 		, ladder.max_ai_count 	] )
		self.rows.append( [ 'min amount players sharing control (controlTeam size)' 	, ladder.min_team_size ] )
		self.rows.append( [ 'max amount of players sharing control (controlTeam size)' 	, ladder.max_team_size ] )
		self.rows.append( [ 'min amount of starting positions (controlTeam count)' 	, ladder.min_team_count ] )
		self.rows.append( [ 'max amount of starting positions (controlTeam count)' 	, ladder.max_team_count ] )
		self.rows.append( [ 'min amount of controlTeams allied' 	, ladder.min_ally_size ] )
		self.rows.append( [ 'max amount of controlTeams allied' 	, ladder.max_ally_size ] )
		self.rows.append( [ 'min amount of ally sides' 	, ladder.min_ally_count ] )
		self.rows.append( [ 'max amount of ally sides' 	, ladder.max_ally_count ] )
		self.rows.append( [ 'ranking algorythm' 	, ladder.ranking_algo_id ] )

class LadderOptionsAdapter:
	def __init__(self,options,ladder):
		self.ladder		= ladder
		self.options 	= options
		self.optheaders	= ['key','value']
		self.bloptions 	= []
		self.wloptions 	= []
		self.admins		= []
		for opt in self.options:
			if opt.key == 'ladderadmin':
				self.admins.append( opt.value )
			else:
				if opt.key == 'modname' or opt.key == 'mapname':
					continue
				if opt.is_whitelist:
					self.wloptions.append( {'key': opt.key, 'value': opt.value } )
				else:
					self.bloptions.append( {'key': opt.key, 'value': opt.value } )

class MatchInfoToTableAdapter:
	def __init__(self, match ):
		self.match = match
		self.rows = []
		self.rows.append( [ 'date'		, match.date] )
		self.rows.append( [ 'modname'	, match.modname] )
		self.rows.append( [ 'mapname'	, match.mapname] )
		self.rows.append( [ 'replay'	, '<a href="%s" >%s</a>'%(match.replay,match.replay.split('/')[-1]) ] )
		self.rows.append( [ 'duration'	, match.duration] )
