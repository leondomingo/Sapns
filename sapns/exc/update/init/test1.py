# -*- coding: utf-8 -*-

from sapns.model.sapnsmodel import SapnsClass
from sapns.model import DBSession as dbs

class Test1(object):
    
    __code__ = u'sapns: test1_py'
    
    def __call__(self):
        
        for cls in dbs.query(SapnsClass):
            cls.description = u'Class: %s' % cls.name
            dbs.add(cls)
            dbs.flush()