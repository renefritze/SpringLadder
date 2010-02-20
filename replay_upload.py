# -*- coding: utf-8 -*-
import pycurl

class Test:
	def __init__(self):
		self.contents = ''

	def body_callback(self, buf):
		self.contents = self.contents + buf

class CurlForm(list):
	def add_string(self, name, str, type=None):
		options = [pycurl.FORM_CONTENTS, str]
		self.__add_optional(options, pycurl.FORM_CONTENTTYPE, type)
		self += (name, tuple(options)),

	def add_file(self, name, file, type=None, filename=None):
		options = [pycurl.FORM_FILE, file]
		self.__add_optional(options, pycurl.FORM_CONTENTTYPE, type)
		self.__add_optional(options, pycurl.FORM_FILENAME, filename)
		self += (name, tuple(options)),

	@staticmethod
	def __add_optional(list, flag, val):
		if val is not None:
			list += flag, val

def postReplay( abs_filepath, lobby_nick, description):
	t = Test()
	c = pycurl.Curl()
	c.setopt(c.POST, 1)
	c.setopt(c.URL, "http://replays.adune.nl/?act=upload&do=upload&secretzon=lamafaarao")
	f = CurlForm()
	f.add_file( 'tiedosto', abs_filepath )
	f.add_string( 'postdata[lobbynick]', lobby_nick )
	if description != '':
		f.add_string( 'postdata[description]', description )
	f.add_string('postdata[replaytype]', "1" ) # 0 - normal game, 1 - ladder
	c.setopt(c.HTTPPOST, f)
	c.setopt(c.WRITEFUNCTION, t.body_callback)
	c.perform()
	c.close()
	return t.contents
