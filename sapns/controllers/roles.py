# -*- coding: utf-8 -*-
"""Users management controller"""

# turbogears imports
from tg import expose, require

# third party imports
from repoze.what import authorize, predicates as p

# project specific imports
from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser , SapnsRole, SapnsUserRole

import logging
from sqlalchemy.sql.expression import and_

__all__ = ['RolesControllers']

class RolesController(BaseController):
    
    allow_only = authorize.not_anonymous()

    @expose('sapns/roles/users.html')
    @require(p.in_group(u'managers'))
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