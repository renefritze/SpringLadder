#!/usr/bin/python
# -*- coding: utf-8 -*-
from jinja2 import Environment, FileSystemLoader
from bottle import route, run, debug, PasteServer, send_file, redirect, abort, request
import ParseConfig, os, index, viewmatch
from customlog import Log
from ladderdb import LadderDB

config = ParseConfig.readconfigfile( 'Main.conf' )
Log.Init( 'website.log', 'website.log' )
db = LadderDB(config['alchemy-uri'])
session = db.getSession()

env = Environment(loader=FileSystemLoader('templates'))

@route('/')
def home():
	return index.output( db, env )

@route('/match')
def match():
	return viewmatch.output( db, env, request )


@route('/static/:filename')
def static_file(filename):
	send_file( filename, root=os.getcwd()+'/static/' )

@route('/demos/:filename')
def static_file(filename):
	send_file( filename, root=os.getcwd()+'/demos/' )

debug(True)
run(server=PasteServer,host='localhost',port=8080, reloader=True)