# -*- coding: utf-8 -*-

from sapns.model.sapnsmodel import SapnsClass, SapnsRole, SapnsPermission
from sapns.model import DBSession as dbs

class UsersRoles(object):
    
    __desc__ = u'init: users/roles'
    
    def __call__(self):
        
        roles = dbs.query(SapnsClass).\
            filter(SapnsClass.name == u'sp_roles').\
            first()
        
        p1 = SapnsPermission()
        p1.class_id = roles.class_id
        p1.permission_name = u'sp_roles#users'
        p1.display_name = u'Users'
        p1.type = SapnsPermission.TYPE_PROCESS
        p1.url = u'/dashboard/roles/users/'
        
        dbs.add(p1)
        
        users = dbs.query(SapnsClass).\
            filter(SapnsClass.name == u'sp_users').\
            first()

        p2 = SapnsPermission()
        p2.class_id = users.class_id
        p2.permission_name = u'sp_users#roles'
        p2.display_name = u'Roles'
        p2.type = SapnsPermission.TYPE_PROCESS
        p2.url = u'/dashboard/users/roles/'
        
        dbs.add(p2)
        dbs.flush()
        
        # "managers" role
        managers = dbs.query(SapnsRole).\
            filter(SapnsRole.group_name == u'managers').\
            first()
        managers.permissions_.append(p1)
        managers.permissions_.append(p2)