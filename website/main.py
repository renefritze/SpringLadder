#!/usr/bin/python
# -*- coding: utf-8 -*-
from bottle import route, run, debug, PasteServer, send_file, redirect, abort
from fieldsets import db
import os, index

@route('/')
def home():
	return index.output( db )

@route('/static/:filename')
def static_file(filename):
	send_file( filename, root=os.getcwd()+'/static/' )

debug(True)
run(server=PasteServer,host='localhost',port=8080)