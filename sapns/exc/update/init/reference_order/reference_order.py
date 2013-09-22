# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs, SapnsPermission, SapnsClass, SapnsRole
from sapns.lib.atenea.const_datos import ROLE_MANAGERS

class ReferenceOrder(object):
    
    __code__ = u'sapns: sp_classes#ref_order'
    
    def __call__(self):
        
        ref_order = SapnsPermission()
        ref_order.permission_name = u'sp_classes#ref_order'
        ref_order.display_name = u'Reference order'
        ref_order.class_id = SapnsClass.by_name(u'sp_classes').class_id
        ref_order.type = SapnsPermission.TYPE_PROCESS
        ref_order.url = u'/dashboard/ref_order/'
        ref_order.requires_id = False
        
        dbs.add(ref_order)
        dbs.flush()
        
        managers = SapnsRole.by_name(ROLE_MANAGERS)
        managers.permissions_.append(ref_order)
        dbs.flush()
