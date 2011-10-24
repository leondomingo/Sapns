# -*- coding: utf-8 -*-

from sapns.model.sapnsmodel import SapnsClass, SapnsRole, SapnsPermission
from base import BaseUpdate

class Privileges(BaseUpdate):
    
    def __call__(self):
        
        dbs = self.dbs
        
        roles = dbs.query(SapnsClass).\
            filter(SapnsClass.name == u'sp_roles').\
            first()
        
        ap_r = SapnsPermission()
        ap_r.class_id = roles.class_id
        ap_r.permission_name = u'sp_roles#privileges'
        ap_r.display_name = u'Privileges'
        ap_r.type = SapnsPermission.TYPE_PROCESS
        ap_r.url = u'/dashboard/privileges/roles/'
        
        dbs.add(ap_r)
        dbs.flush()
        
        # "managers" role
        managers = dbs.query(SapnsRole).\
            filter(SapnsRole.group_name == u'managers').\
            first()
            
        managers.permissions_.append(ap_r)

update = Privileges