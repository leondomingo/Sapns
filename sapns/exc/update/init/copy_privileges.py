# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsClass, SapnsRole, SapnsPermission 

class CopyPrivileges(object):
    
    __code__ = u'init: copy privileges'
    
    def __call__(self):
        
        roles = dbs.query(SapnsClass).\
            filter(SapnsClass.name == u'sp_roles').\
            first()
        
        ap_r = SapnsPermission()
        ap_r.class_id = roles.class_id
        ap_r.permission_name = u'sp_roles#copy_privileges'
        ap_r.display_name = u'Copy privileges'
        ap_r.type = SapnsPermission.TYPE_PROCESS
        ap_r.url = u'/dashboard/privileges/copy/'
        
        dbs.add(ap_r)
        
        # "managers" role
        managers = dbs.query(SapnsRole).\
            filter(SapnsRole.group_name == u'managers').\
            first()
        managers.permissions_.append(ap_r)