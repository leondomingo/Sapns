# -*- coding: utf-8 -*-

from sapns.model.sapnsmodel import SapnsClass, SapnsRole, SapnsPermission
from base import BaseUpdate

class CopyPrivileges(BaseUpdate):
    
    def __call__(self):
        
        dbs = self.dbs
        
        roles = SapnsClass.by_name(u'sp_roles')
        
        ap_r = SapnsPermission()
        ap_r.class_id = roles.class_id
        ap_r.permission_name = u'sp_roles#copy_privileges'
        ap_r.display_name = u'Copy privileges'
        ap_r.type = SapnsPermission.TYPE_PROCESS
        ap_r.url = u'/dashboard/privileges/copy/'
        
        dbs.add(ap_r)
        
        # "managers" role
        managers = SapnsRole.by_name(u'managers')
        managers.permissions_.append(ap_r)

update = CopyPrivileges()