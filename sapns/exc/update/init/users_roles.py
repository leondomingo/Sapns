# -*- coding: utf-8 -*-

from sapns.model.sapnsmodel import SapnsClass, SapnsRole, SapnsPermission
from base import BaseUpdate

class UsersRoles(BaseUpdate):
    
    def __call__(self):
        
        dbs = self.dbs
        
        roles = SapnsClass.by_name(u'sp_roles')
        
        p1 = SapnsPermission()
        p1.class_id = roles.class_id
        p1.permission_name = u'sp_roles#users'
        p1.display_name = u'Users'
        p1.type = SapnsPermission.TYPE_PROCESS
        p1.url = u'/dashboard/roles/users/'
        
        dbs.add(p1)
        
        users = SapnsClass.by_name(u'sp_users')

        p2 = SapnsPermission()
        p2.class_id = users.class_id
        p2.permission_name = u'sp_users#roles'
        p2.display_name = u'Roles'
        p2.type = SapnsPermission.TYPE_PROCESS
        p2.url = u'/dashboard/users/roles/'
        
        dbs.add(p2)
        dbs.flush()
        
        # "managers" role
        managers = SapnsRole.by_name(u'managers')
        managers.permissions_.append(p1)
        managers.permissions_.append(p2)

update = UsersRoles