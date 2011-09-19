# -*- coding: utf-8 -*-
"""Users management controller"""

# turbogears imports
from tg import expose, url, config, redirect, require, request

# third party imports
from pylons import cache
from pylons.i18n import ugettext as _
from pylons.i18n import lazy_ugettext as l_
from repoze.what import authorize, predicates

# project specific imports
from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs

import logging
import simplejson as sj
from sapns.model.sapnsmodel import SapnsUser , SapnsRole, SapnsUserRole,\
    SapnsPermission, SapnsRolePermission
from neptuno.dataset import DataSet
from neptuno.util import get_paramw, strtobool
from neptuno.postgres.search import search
from urllib import urlencode
from sqlalchemy.sql.expression import and_

__all__ = ['RolesControllers']

class RolesController(BaseController):
    
    allow_only = authorize.not_anonymous()

    @expose('sapns/roles/users.html')
    @require(predicates.has_any_permission('manage', 'users'))
    def users(self, id_role, **kw):

        logger = logging.getLogger('RolesController.roles')        
        try:
            role = dbs.query(SapnsRole).get(int(id_role))
            
            users = []
            for u in dbs.query(SapnsUser):
                #u = SapnsUser()
                
                has_role = dbs.query(SapnsUserRole).\
                    filter(and_(SapnsUserRole.role_id == role.group_id,
                                SapnsUserRole.user_id == u.user_id,
                                )).\
                    first()
                
                users.append(dict(id=u.user_id,
                                  name=u.user_name,
                                  selected=has_role != None,
                                  ))

#            for i in xrange(50):
#                users.append(dict(id=0, name='xxxx', selected=False))
                
            permissions = []
            for p in dbs.query(SapnsPermission).\
                    filter(SapnsPermission.class_id == None).\
                    order_by(SapnsPermission.permission_name):
                
                has_permission = dbs.query(SapnsRolePermission).\
                    filter(and_(SapnsRolePermission.role_id == role.group_id,
                                SapnsRolePermission.permission_id == p.permission_id,
                                )).\
                    first()
                
                permissions.append(dict(id=p.permission_id,
                                        name=p.permission_name,
                                        selected=has_permission != None,
                                        ))
                
            
            return dict(page='Role users', came_from=kw.get('came_from'),
                        role=dict(id=role.group_id, name=role.group_name), 
                        users=users, permissions=permissions)
            
        except Exception, e:
            logger.error(e)