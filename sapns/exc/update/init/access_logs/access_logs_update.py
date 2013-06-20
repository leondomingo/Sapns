# -*- coding: utf-8 -*-

from sapns.lib.sapns.mongo import Mongo
import logging

class AccessLogsUpdate(object):

    __code__ = u'access logs update (1)'

    def __call__(self):

        logger = logging.getLogger('AccessLogsUpdate')

        mdb = Mongo().db

        for row in mdb['access'].find():

            logger.info(row['when'])
            
            when_ = row['when']
            when = dict(date=str(when_.date()),
                        time=str(when_.time()))

            mdb['access'].update(dict(_id=row['_id']),
                                 { '$set': dict(when_=when_, when=when) })
