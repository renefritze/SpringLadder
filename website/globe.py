# -*- coding: utf-8 -*-
from customlog import Log
from jinja2 import Environment, FileSystemLoader
import ParseConfig
from ladderdb import LadderDB
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

cache_opts = {
    'cache.type': 'memory',
    'cache.data_dir': 'tmp/cache/data',
    'cache.lock_dir': 'tmp/cache/lock'
}

config = ParseConfig.readconfigfile( 'Main.conf' )
Log.Init( 'website.log', 'website.log' )
db = LadderDB(config['alchemy-uri'])
env = Environment(loader=FileSystemLoader('templates'))
staging = 'staging' in config.keys()
cache = CacheManager(**parse_cache_config_options(cache_opts))
