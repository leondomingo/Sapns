# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsRole, SapnsClass
import logging

class TM_Test(object):
    
    #__code__ = u'init: tm_test'
    
    def __call__(self):
        
        logger = logging.getLogger('TM_Test')
        
        managers = SapnsRole.by_name(u'managers')
        for usuario in managers.users_:
            
            logger.info(usuario.display_name)
            db = usuario.get_dashboard()
            for sc in db.children:
                logger.info(sc.title)
                sc.title = '_%s' % sc.title
                dbs.add(sc)
                dbs.flush()
                
        def attributes(cls):
            for attr in cls.attributes:
                logger.info(attr.name)
                attr.title = '*%s' % attr.title
                dbs.add(attr)
                dbs.flush()
                
        attributes(SapnsClass.by_name(u'alumnos'))
        attributes(SapnsClass.by_name(u'clientes'))
