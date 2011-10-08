# -*- coding: utf-8 -*-

from sapns.model.sapnsmodel import SapnsClass
from base import BaseUpdate

class Test1(BaseUpdate):
    
    def __call__(self):
        
        dbs = self.dbs
        
        for cls in dbs.query(SapnsClass):
            cls.description = u'Class: %s' % cls.name
            dbs.add(cls)
            dbs.flush()

update = Test1