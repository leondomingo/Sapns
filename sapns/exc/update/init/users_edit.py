# -*- coding: utf-8 -*-

from sapns.model.sapnsmodel import SapnsPermission
from base import BaseUpdate

class UsersEdit(BaseUpdate):
    
    def __call__(self):
        
        dbs = self.dbs
        
        # sp_users#new
        p_new = dbs.query(SapnsPermission).\
            filter(SapnsPermission.permission_name == u'sp_users#new').\
            first()
            
        p_new.url = u'/dashboard/users/new/'
        p_new.requires_id = False
        
        dbs.add(p_new)
        dbs.flush()
        
        # sp_users#new
        p_edit = dbs.query(SapnsPermission).\
            filter(SapnsPermission.permission_name == u'sp_users#edit').\
            first()
            
        p_edit.url = u'/dashboard/users/edit/'
        p_edit.requires_id = True
        
        dbs.add(p_edit)
        dbs.flush()

update = UsersEdit