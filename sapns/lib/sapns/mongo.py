# -*- coding: utf-8 -*-

from tg import config
import pymongo
import re

def _mongo_setting(setting_name):
    return 'mongodb.%s' % setting_name

class Mongo(object):
    
    def __init__(self):
        
        DEFAULT_PORT = 27017
        
        mongodb_url = config.get(_mongo_setting('url'))
        m = re.search(r'^([^:]+)(:\d+)?$', mongodb_url)
        if m:
            mongo_host = m.group(1)
            mongo_port = int(m.group(2) or DEFAULT_PORT)
            self.conn = pymongo.MongoClient(mongo_host, mongo_port)
            self.db = self.conn[config.get(_mongo_setting('dbname'))]