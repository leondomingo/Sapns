# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsPermission, SapnsClass, SapnsRole

class CreateShortcutsFromPermissions(object):
    
    __code__ = u'sapns: create shortcuts from permissions'
    
    def __call__(self):
        
        csfp = SapnsPermission()
        csfp.class_id = SapnsClass.by_name(u'sp_permission').class_id
        csfp.permission_name = u'sp_permission#create_shortcuts'
        csfp.display_name = u'Create shortcuts'
        csfp.type = SapnsPermission.TYPE_PROCESS
        csfp.url = u'/dashboard/permissions/create_shortcuts/'
        csfp.requires_id = True
        
        dbs.add(csfp)
        dbs.flush()
        
        managers = SapnsRole.by_name(u'managers')
        managers.permissions_.append(csfp)
        dbs.flush()