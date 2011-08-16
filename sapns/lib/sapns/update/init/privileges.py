# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs #@UnusedImport
from sapns.model.sapnsmodel import SapnsClass, SapnsRole, SapnsPermission

class Privileges(object):
    
    def __call__(self):
        
        roles = SapnsClass.by_name(u'sp_roles')
        
        ap_r = SapnsPermission()
        ap_r.class_id = roles.class_id
        ap_r.permission_name = u'sp_roles#privileges'
        ap_r.display_name = u'Privileges'
        ap_r.type = SapnsPermission.TYPE_PROCESS
        ap_r.url = u'/dashboard/privileges/roles/'
        
        dbs.add(ap_r)
        
#        users = SapnsClass.by_name(u'sp_users')
#        
#        ap_u = SapnsPermission()
#        ap_u.class_id = users.class_id
#        ap_u.permission_name = u'sp_users#privileges'
#        ap_u.display_name = u'Privileges'
#        ap_u.type = SapnsPermission.TYPE_PROCESS
#        ap_u.url = u'/dashboard/privileges/users/'
#        
#        dbs.add(ap_r)
#        dbs.flush()
        
        # "managers" role
        managers = SapnsRole.by_name(u'managers')
        managers.permissions_.append(ap_r)
        #managers.permissions_.append(ap_u)

update = Privileges()