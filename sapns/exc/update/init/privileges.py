# -*- coding: utf-8 -*-

from sapns.model.sapnsmodel import SapnsClass, SapnsRole, SapnsPermission
from base import BaseUpdate

class Privileges(BaseUpdate):
    
    def __call__(self):
        
        dbs = self.dbs
        
        roles = SapnsClass.by_name(u'sp_roles')
        
        ap_r = SapnsPermission()
        ap_r.class_id = roles.class_id
        ap_r.permission_name = u'sp_roles#privileges'
        ap_r.display_name = u'Privileges'
        ap_r.type = SapnsPermission.TYPE_PROCESS
        ap_r.url = u'/dashboard/privileges/roles/'
        
        dbs.add(ap_r)
        
        # "managers" role
        managers = SapnsRole.by_name(u'managers')
        managers.permissions_.append(ap_r)

update = Privileges()