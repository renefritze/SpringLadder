#!/usr/bin/python
# -*- coding: utf-8 -*-
from bottle import route, run, debug, PasteServer, send_file, redirect, abort, request, default_app
import os, index, viewmatch, viewplayer, viewladder, viewrules, \
	help, fame, scoreboard, change_ladder,adminindex, recalc, deleteladder, \
	adminmatch
from globe import config,staging

@route('/static/:filename')
def static_file(filename):
	return send_file( filename, root=os.getcwd()+'/static/' )

@route('/demos/:filename')
def demos(filename):
	return send_file( filename, root=os.getcwd()+'/demos/' )

@route('/favicon.ico')
def favi():
	return send_file( 'favicon.ico', root=os.getcwd()+'/images/' )

if __name__=="__main__":
	port = config['port']
	debug(staging)
	app = default_app()
	run(app=app,server=PasteServer,host='localhost',port=port , reloader=False)