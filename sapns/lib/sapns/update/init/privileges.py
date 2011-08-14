# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs #@UnusedImport
from sapns.model.sapnsmodel import SapnsClass, SapnsAction, SapnsRole

class Privileges(object):
    
    def __call__(self):
        
        roles = SapnsClass.by_name(u'sp_roles')
        
        ap_r = SapnsAction()
        ap_r.class_id = roles.class_id
        ap_r.name = u'Privileges'
        ap_r.type = SapnsAction.TYPE_PROCESS
        ap_r.url = u'/dashboard/privileges/roles/'
        
        dbs.add(ap_r)
        
        users = SapnsClass.by_name(u'sp_users')
        
        ap_u = SapnsAction()
        ap_u.class_id = users.class_id
        ap_u.name = u'Privileges'
        ap_u.type = SapnsAction.TYPE_PROCESS
        ap_r.url = u'/dashboard/privileges/users/'
        
        dbs.add(ap_r)
        dbs.flush()
        
        # "managers" role
        managers = SapnsRole.by_name(u'managers')
        #managers = SapnsRole()
        managers.add_act_privilege(ap_r.action_id)
        managers.add_act_privilege(ap_u.action_id)

update = Privileges()