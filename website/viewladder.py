#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgi
from jinja2 import Environment, FileSystemLoader
from fieldsets import *
from formalchemy import Field, types
import cgitb
cgitb.enable()
env = Environment(loader=FileSystemLoader('templates'))

#class ReducedLadder:
	#player_count,match_count,name,id,ranks,description,last_match

id = getSingleField( 'id' )
try:
	if not id:
		s = db.sessionmaker()
		ladder_list = []
		ladder_triple_list = s.query(Ladder)
		#ladder_triple_list = [db.GetLadder( 17 )]
		for  l in ladder_triple_list:
			ladder_id = l.id
			ladder_name = l.name
			ladder_description = l.description
			player_count = s.query( Result.id ).group_by( Result.player_id ).\
				filter(Result.ladder_id == ladder_id).count()
			match_query = s.query( Match.id,Match.date,Match.mapname ).\
				filter(Match.ladder_id == ladder_id)
			match_count = match_query.count()
			last_match = match_query.order_by( Match.date.desc() ).first()

			item = dict()
			item['player_count'] = player_count
			item['match_count'] = match_count
			item['last_match'] = last_match
			item['name'] = ladder_name
			item['description'] = ladder_description
			item['id'] = ladder_id
			try:
				ranks = db.GetRanks( ladder_id, None, 3 )
				item['ranks'] = GlobalRankingAlgoSelector.GetWebRepresentation( ranks, db )
			except Exception, e:
				item['ranks'] = None
			ladder_list.append( item )
		template = env.get_template('viewladderlist.html')
		print template.render(ladders=ladder_list )
	else:
		ladder = db.GetLadder( id )
		template = env.get_template('viewladder.html')
		ranks = db.GetRanks( id, None, 10 )
		rank_table = GlobalRankingAlgoSelector.GetWebRepresentation( ranks, db )
		print template.render(ladder=ladder, rank_table=rank_table )

except ElementNotFoundException, e:
	template = env.get_template('error.html')
	print template.render( err_msg="ladder with id %s not found"%(str(id)) )
except EmptyRankingListException, m:
	template = env.get_template('error.html')
	print template.render( err_msg=(str(m)) )