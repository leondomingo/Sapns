# -*- coding: utf-8 -*-

from tg import config
import pymongo
import re

SCHEDULED_TASKS             = 'scheduled_tasks'
SCHEDULED_TASKS_ATTACHMENTS = 'scheduled_tasks_attachments'

PENDING     = 0
IN_PROGRESS = 1
SUCCESS     = 2
ERROR       = -1


class Mongo(object):

    def __init__(self):

        DEFAULT_PORT = 27017

        mongodb_url = config.get(self.mongo_setting('url'))
        # localhost
        # localhost:27017
        # 100.100.100.100
        # 100.100.100.100:28987
        m = re.search(r'^([^:]+)(:\d+)?$', mongodb_url)
        if m:
            mongo_host = m.group(1)
            mongo_port = int(m.group(2) or DEFAULT_PORT)
            self.conn = pymongo.MongoClient(mongo_host, mongo_port)
            self.db = self.conn[config.get(self.mongo_setting('dbname'))]

    def mongo_setting(self, setting_name):
        return 'mongodb.%s' % setting_name
