#!/usr/bin/python
# -*- coding: utf-8 -*-

from fieldsets import getSingleField
from ladderdb import ElementNotFoundException, EmptyRankingListException
from db_entities import Ladder, Match, Result
from ranking import GlobalRankingAlgoSelector

def output( db, env, request ):
	id = getSingleField( 'id', request )
	try:
		s = db.sessionmaker()
		if not id:
			ladder_list = []
			ladder_triple_list = s.query(Ladder).order_by( Ladder.name )
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
			s.close()
			return template.render(ladders=ladder_list )
		else:
			ladder = db.GetLadder( id )
			template = env.get_template('viewladder.html')
			limit = 10
			ranks = db.GetRanks( id, None, limit )
			matches = s.query( Match ).filter( Match.ladder_id == id ).order_by(Match.date.desc())[:limit]
			rank_table = GlobalRankingAlgoSelector.GetWebRepresentation( ranks, db )
			s.close()
			return template.render(ladder=ladder, rank_table=rank_table, matches=matches )

	except ElementNotFoundException, e:
		template = env.get_template('error.html')
		s.close()
		return template.render( err_msg="ladder with id %s not found"%(str(id)) )
	except EmptyRankingListException, m:
		template = env.get_template('error.html')
		s.close()
		return template.render( err_msg=(str(m)) )