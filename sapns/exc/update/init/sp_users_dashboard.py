# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs, SapnsClass, SapnsPermission, SapnsRole

class SpUsersDashboard(object):
    
    __code__ = u'sp_users#dashboard'
    
    def __call__(self):
        
        dashboard = SapnsPermission()
        dashboard.permission_name = u'sp_users#dashboard'
        dashboard.display_name = u'Dashboard'
        dashboard.description = u'Allow a manager to modify the dashboard of another user'
        dashboard.url = u'/dashboard/users/dashboard/'
        dashboard.type = SapnsPermission.TYPE_PROCESS
        dashboard.class_id = SapnsClass.by_name(u'sp_users').class_id
        dashboard.requires_id = True
        
        dbs.add(dashboard)
        dbs.flush()
        
        managers = SapnsRole.by_name(u'managers')
        managers.permissions_.append(dashboard)
        dbs.flush()