#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from sapns.model import DBSession as dbs

def test1(*args, **kwargs):
    logger = logging.getLogger('test1')
    logger.info('test1')
    print args, kwargs
    
def test2(one, two, three=None):
    
    from sapns.model import SapnsClass
    
    logger = logging.getLogger('test2')
    logger.info('test2')
    print one, two, three
    
    for cls in dbs.query(SapnsClass).order_by(SapnsClass.name).limit(10):
        print u'%s (%s)' % (cls.title, cls.name)
    
class Test(object):
    
    def __init__(self, one, two, three=None):
        self.one = one
        self.two = two
        self.three = three
        
    def __call__(self):
        logger = logging.getLogger('Test')
        logger.info('Test')
        print self.one, self.two, self.three