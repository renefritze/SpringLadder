#!/usr/bin/python
# -*- coding: utf-8 -*-
from jinja2 import Environment, FileSystemLoader
from bottle import route, run, debug, PasteServer, send_file, redirect, abort, request, default_app
import ParseConfig, os, index, viewmatch, viewplayer, viewladder, viewrules, \
	help, fame, scoreboard, change_ladder,adminindex, recalc
from customlog import Log
from ladderdb import LadderDB
from auth import AuthDecorator
from db_entities import Roles

config = ParseConfig.readconfigfile( 'Main.conf' )
Log.Init( 'website.log', 'website.log' )
db = LadderDB(config['alchemy-uri'])
env = Environment(loader=FileSystemLoader('templates'))
staging = 'staging' in config.keys()

@route('/')
def home():
	return index.output( db, env )

@route('/match')
def match():
	return viewmatch.output( db, env, request )

@route('/player')
def player():
	return viewplayer.output( db, env, request )

@route('/ladder')
def ladder():
	return viewladder.output( db, env, request )

@route('/rules')
def rules():
	return viewrules.output( db, env, request )

@route('/scoreboard')
def scoreboard_():
	return scoreboard.output( db, env, request )

@route('/help')
def help_():
	return help.output( db, env, request )

@route('/admin', method='GET')
@AuthDecorator( Roles.User, db )
def adminindex_():
	return adminindex.output( db, env, request )
@route('/admin', method='POST')
@AuthDecorator( Roles.User, db )
def adminindexp_():
	return adminindex.output( db, env, request )

@route('/admin/ladder', method='POST')
@AuthDecorator( Roles.User, db )
def admin_ladder():
	return change_ladder.output( db, env, request )
@route('/admin/ladder', method='GET')
@AuthDecorator( Roles.User, db )
def admin_ladder_():
	return change_ladder.output( db, env, request )

@route('/admin/recalc', method='GET')
@AuthDecorator( Roles.User, db )
def recalc_():
	return recalc.output( db, env, request )

@route('/fame')
def fame_():
	return fame.output( db, env, request )

@route('/static/:filename')
def static_file(filename):
	return send_file( filename, root=os.getcwd()+'/static/' )

@route('/demos/:filename')
def demos(filename):
	return send_file( filename, root=os.getcwd()+'/demos/' )

port = config['port']
debug(staging)
app = default_app()
run(app=app,server=PasteServer,host='localhost',port=port , reloader=False)