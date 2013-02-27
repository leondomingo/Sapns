# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs, SapnsPermission, SapnsRole

class DashboardManagement(object):
    
    __code__ = u'sapns. dashboard-management'
    
    def __call__(self):
        
        dm = SapnsPermission()
        dm.permission_name = u'dashboard-management'
        dm.display_name = u'Dashboard Management'
        dm.description = u'Dashboard management'
        dm.requires_id = False
        
        dbs.add(dm)
        dbs.flush()
        
        # assign to every role
        for r in dbs.query(SapnsRole):
            r.permissions_.append(dm)
            dbs.flush()