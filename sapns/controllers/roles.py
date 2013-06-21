# -*- coding: utf-8 -*-
"""Users management controller"""

from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser, SapnsRole, SapnsUserRole
from sqlalchemy.sql.expression import and_
from tg import expose, require, predicates as p
import logging
from sapns.lib.sapns.util import add_language

__all__ = ['RolesController']

class RolesController(BaseController):
    
    allow_only = p.not_anonymous()

    @expose('sapns/roles/users.html')
    @require(p.in_group(u'managers'))
    @add_language
    def users(self, id_role, **kw):

        logger = logging.getLogger('RolesController.roles')        
        try:
            role = dbs.query(SapnsRole).get(int(id_role))
            
            users = []
            for u in dbs.query(SapnsUser):
                
                has_role = dbs.query(SapnsUserRole).\
                    filter(and_(SapnsUserRole.role_id == role.group_id,
                                SapnsUserRole.user_id == u.user_id,
                                )).\
                    first()
                
                users.append(dict(id=u.user_id,
                                  name=u.user_name,
                                  selected=has_role != None,
                                  ))

            return dict(page='Role users', came_from=kw.get('came_from'),
                        role=dict(id=role.group_id, name=role.group_name), 
                        users=users)
            
        except Exception, e:
            logger.error(e)
