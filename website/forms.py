# -*- coding: utf-8 -*-
from wtforms import Form, BooleanField, TextField, validators, FieldList, \
	FormField, HiddenField, BooleanField, IntegerField, SelectField, widgets

import ranking

def tupleizelist( alist ):
	r = []
	for l in alist:
		r.append( (l,l) )
	return r

class Option(Form):
	id				= HiddenField('id', [validators.Required(),validators.NumberRange(1)] )
	ladder_id 		= HiddenField('ladder_id', [validators.Required(),validators.NumberRange(1)] )
	key 			= TextField('key',[validators.Length(max=100), validators.Required()])
	value 			= TextField('value',[validators.Length(max=100), validators.Required()])
	is_whitelist 	= BooleanField('is_whitelist' )
	#adminkey		= 'ladderadmin'

class OptionWidget(object):
	def __init__(self, with_table_tag=False):
		self.with_table_tag = with_table_tag

	def __call__(self, field, **kwargs):
		html = []
		if self.with_table_tag:
			kwargs.setdefault('id', field.id)
			html.append(u'<table %s>' % html_params(**kwargs))
		hidden = u''
		errors = ''
		i = 0
		for subfield in field:
			if subfield.type == 'HiddenField':
				hidden += unicode(subfield)
			else:
				if i == 4:
					del_button = '<input type="submit" name="delete_%s" value="delete"/>'%field.id
					html.append(u'<td>%s%s</td>' % (unicode(subfield),del_button) )
				else:
					html.append(u'<td>%s</td>' % unicode(subfield))
				errors += ', '.join(subfield.errors)
			i += 1
		html.append(u'<td>%s</td>' % unicode(errors))
		if self.with_table_tag:
			html.append(u'</table>')
		if hidden:
			html.append(hidden)
		return u''.join(html)

class Ladder(Form):
	id				= HiddenField('id', [validators.Required(),validators.NumberRange(1)] )
	name 			= TextField('name',[validators.Length(min=4, max=100), validators.Required()])
	description 	= TextField('description', [validators.Optional()] )
	min_team_size 	= IntegerField('min_team_size', [validators.NumberRange(1,256)] )
	max_team_size 	= IntegerField('max_team_size', [validators.NumberRange(1,256)] )
	min_ally_size 	= IntegerField('min_ally_size', [validators.NumberRange(1,256)] )
	max_ally_size 	= IntegerField('max_ally_size', [validators.NumberRange(1,256)] )
	min_ally_count 	= IntegerField('min_ally_count', [validators.NumberRange(1,256)] )
	max_ally_count 	= IntegerField('max_ally_count', [validators.NumberRange(1,256)] )
	min_team_count 	= IntegerField('min_team_count', [validators.NumberRange(1,256)] )
	max_team_count 	= IntegerField('max_team_count', [validators.NumberRange(1,256)] )
	min_ai_count	= IntegerField('min_ai_count', [validators.NumberRange(0,256)] )
	max_ai_count	= IntegerField('max_ai_count', [validators.NumberRange(0,256)] )
	
	ranking_algo_id	= SelectField('ranking_algo_id',choices=tupleizelist(ranking.RankingAlgoSelector.available_ranking_algos), \
		validators=[validators.Required(), validators.AnyOf(ranking.RankingAlgoSelector.available_ranking_algos)] )

	options			= FieldList( FormField(Option, widget=OptionWidget()) )

	field_order = ['name','description','min_team_size','max_team_size','min_ally_size','max_ally_size',\
		'min_team_count','max_team_count','min_ally_count','max_ally_count','min_ai_count','max_ai_count',\
		'ranking_algo_id','id']

#class Player(Base):
	#__tablename__ 	= 'players'
	#id 				= Column( Integer, primary_key=True )
	#server_id		= Column( Integer, index=True )
	#nick 			= Column( String(50),index=True )
	#pwhash 			= Column( String(80) )
	#role			= Column( Integer )
	#do_hide_results = Column( Boolean )

	#def __init__(self, nick='noname', role=Roles.User, pw=''):
		#self.nick 		= nick
		#self.role 		= role
		#do_hide_results = False
		#self.server_id		= -1
	#def __str__(self):
		#return "Player(id:%d,server_id:%d) %s "%(self.id, self.server_id, self.nick)

	#def validate( self, password ):
		#if self.pwhash == '':
			#return False
		#return self.pwhash == hashlib.sha224(password).hexdigest()

	#def SetPassword( self, password ):
		#self.pwhash = hashlib.sha224(password).hexdigest()

#class Match(Base):
	#__tablename__ 	= 'matches'
	#id 				= Column( Integer, primary_key=True )
	#ladder_id 		= Column( Integer, ForeignKey( Ladder.id ),index=True )
	#date 			= Column( DateTime )
	#modname 		= Column( String( 60 ) )
	#mapname 		= Column( String( 60 ) )
	#replay 			= Column( String( 200 ) )
	#duration 		= Column( Interval )
	#last_frame		= Column( Integer )

	#settings    	= relation("MatchSetting", 	order_by="MatchSetting.key" )#, backref="match" )#this would auto-create a relation in MatchSetting too
	#results			= relation("Result", 		order_by="Result.died" )
	#ladder			= relation("Ladder" )


#class MatchSetting(Base):
	#__tablename__ 	= 'matchsettings'
	#id 				= Column( Integer, primary_key=True )
	#key 			= Column( String(40) )
	#value 			= Column( String(80) )
	#match_id 		= Column( Integer, ForeignKey( Match.id ),index=True )

#class Result(Base):
	#__tablename__ 	= 'results'
	#id 				= Column( Integer, primary_key=True )
	#player_id 		= Column( Integer, ForeignKey( Player.id ) )
	#match_id 		= Column( Integer, ForeignKey( Match.id ) )
	#ladder_id 		= Column( Integer, ForeignKey( Ladder.id ),index=True )
	#date 			= Column( DateTime )
	#team			= Column( Integer )
	#ally			= Column( Integer )
	#disconnect		= Column( Integer )
	#quit			= Column( Boolean )
	#died			= Column( Integer )
	#desync			= Column( Integer )
	#timeout			= Column( Boolean )
	#kicked			= Column( Boolean )
	#connected		= Column( Boolean )

	#player			= relation(Player)
	#match			= relation(Match)

	#def __init__(self):
		#self.team 		= -1
		#self.disconnect = -1
		#self.ally		= -1
		#self.died		= -1
		#self.desync		= -1
		#self.timeout	= False
		#self.connected	= False
		#self.quit		= False
		#self.kicked		= False

#class Bans(Base):
	#__tablename__	= 'bans'
	#id 				= Column( Integer, primary_key=True )
	#player_id 		= Column( Integer, ForeignKey( Player.id ) )
	#ladder_id 		= Column( Integer, ForeignKey( Ladder.id ) )
	#end				= Column( DateTime )

	#player			= relation("Player")
	#ladder			= relation('Ladder')

	#def __str__(self):
		#if self.ladder_id != -1:
			#ret = '%s on Ladder %s: %s remaining'%( self.player.nick,self.ladder.name,str(self.end - datetime.now() ) )
		#else:
			#ret = '%s (global ban): %s remaining'%( self.player.nick,str(self.end - datetime.now() ) )
		#return ret


#"""this does not actually work, but should only show what's min for new tables
#class IRanks(Base):
	#id 				= Column( Integer, primary_key=True )
	#player_id 		= Column( Integer, ForeignKey( Player.id ) )
	#ladder_id 		= Column( Integer, ForeignKey( Ladder.id ) )
#"""
#class SimpleRanks(Base):
	#__tablename__	= 'simpleranks'
	#id 				= Column( Integer, primary_key=True )
	#player_id 		= Column( Integer, ForeignKey( Player.id ) )
	#ladder_id 		= Column( Integer, ForeignKey( Ladder.id ),index=True )
	#points			= Column( Integer )

	#def __init__(self):
		#self.points = 0

	#player			= relation("Player")

	#def __str__(self):
		#return '%d points'%self.points

#class GlickoRanks(Base):
	#__tablename__	= 'glickoranks'
	#id 				= Column( Integer, primary_key=True )
	#player_id 		= Column( Integer, ForeignKey( Player.id ) )
	#ladder_id 		= Column( Integer, ForeignKey( Ladder.id ),index=True )
	#rating			= Column( Float )
	#rd				= Column( Float )

	#def __init__(self):
		#self.rating = 1500
		#self.rd		=  350

	#player			= relation("Player")

	#def __str__(self):
		#return '%f/%f (rating/rating deviation)'%(self.rating,self.rd)

#class Config(Base):
	#__tablename__	= 'config'
	#dbrevision		= Column( Integer, primary_key=True )

	#def __init__(self):
		#self.dbrevision = 1
