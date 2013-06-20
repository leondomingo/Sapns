# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs, SapnsPermission, SapnsClass, SapnsRole
from sapns.lib.atenea.const_datos import ROLE_MANAGERS

class AccessLogs(object):
    
    __code__ = u'access-logs'
    
    def __call__(self):
        
        access_logs = SapnsPermission()
        access_logs.permission_name = u'access-logs'
        access_logs.display_name = u'Access logs'
        #access_logs.class_id = SapnsClass.by_name(u'').class_id
        access_logs.type = SapnsPermission.TYPE_PROCESS
        access_logs.url = u'/dashboard/logs/'
        access_logs.requires_id = False
        
        dbs.add(access_logs)
        dbs.flush()
        
        managers = SapnsRole.by_name(ROLE_MANAGERS)
        managers.permissions_.append(access_logs)
        dbs.flush()
