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

        mongodb_url = config.get(self.mongo_setting('url'))
        # localhost
        # localhost:27017
        # 100.100.100.100
        # 100.100.100.100:28987
        # mongodb://foo.bar.com:39768/dbname
        # mongodb://user:password@foo.bar.com:39768/dbname
        self.conn = pymongo.MongoClient(mongodb_url)
        m_dbname = re.search(r'/(\w+)$', mongodb_url)
        if m_dbname:
            dbname = m_dbname.group(1)

        else:
            dbname = config.get(self.mongo_setting('dbname'))

        self.db = self.conn[dbname]

    def mongo_setting(self, setting_name):
        return 'mongodb.%s' % setting_name
