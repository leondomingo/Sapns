# -*- coding: utf-8 -*-
"""Users management controller"""

# turbogears imports
from tg import expose, url, redirect, require, request

# third party imports
from pylons import cache
from pylons.i18n import ugettext as _
from repoze.what import authorize, predicates

# project specific imports
from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs

import logging
import simplejson as sj
from sapns.model.sapnsmodel import SapnsUser , SapnsRole, SapnsUserRole
from neptuno.util import get_paramw, strtobool
from sqlalchemy.sql.expression import and_

__all__ = ['UsersControllers']

class UsersController(BaseController):
    
    allow_only = authorize.not_anonymous()
    
    @expose('sapns/users/edit.html')
    @require(predicates.not_anonymous())
    def edit(self, cls, id, **params):
        
        user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
        id_user = int(id)
        
        is_manager = u'managers' in request.identity['groups']
        
        if user.user_id != id_user and not is_manager:
            redirect(url('/error'))
        
        came_from = params.get('came_from')
        if came_from:
            came_from = url(came_from)
        
        user = dbs.query(SapnsUser).get(id_user)
        return dict(user=user, came_from=came_from)
    
    @expose('sapns/users/edit.html')
    @require(predicates.has_any_permission('manage', 'users'))
    def new(self, cls, **params):
        came_from = params.get('came_from', '/dashboard/users')
        return dict(user={}, came_from=url(came_from))
    
    @expose()
    @require(predicates.has_any_permission('manage', 'users'))
    def save(self, **params):
        
        came_from = params.get('came_from')
        if came_from:
            came_from = url(came_from)
            
        try:
            new_user = False
            if params['id']:
                user = dbs.query(SapnsUser).get(params['id'])
            else:
                new_user = True
                user = SapnsUser()
                
            user.display_name = params['display_name']
            user.user_name = params['user_name']
            user.email_address = params['email_address']
            
            if params['password'] != '':
                user.password = params['password']
                
            dbs.add(user)
            dbs.flush()
            
            # copy shortcuts and privileges form another user
            if new_user:
                user.copy_from(int(params['copy_from']))
        
        except:
            redirect(url('/message', 
                         params=dict(message=_('An error occurred while saving the user'),
                                     came_from=came_from)))

        if came_from:
            redirect(came_from)
            
        else:
            redirect(url('/message',
                         params=dict(message='User was updated successfully',
                                     came_from='')))

    @expose('sapns/users/permission.html')
    @require(predicates.has_any_permission('manage', 'users'))
    def permission(self, came_from='/dashboard/users'):
        return dict(came_from=url(came_from))
    
    @expose('sapns/users/roles.html')
    @require(predicates.has_any_permission('manage', 'users'))
    def roles(self, id_user, **kw):

        logger = logging.getLogger('UsersController.roles')        
        try:
            user = dbs.query(SapnsUser).get(int(id_user))
            
            roles = []
            for r in dbs.query(SapnsRole).order_by(SapnsRole.group_name):
                #r = SapnsRole()
                
                has_role = dbs.query(SapnsUserRole).\
                    filter(and_(SapnsUserRole.role_id == r.group_id,
                                SapnsUserRole.user_id == user.user_id,
                                )).\
                    first()
                
                roles.append(dict(id=r.group_id,
                                  name=r.group_name,
                                  selected=has_role != None,
                                  ))
                
#            for i in xrange(50):
#                roles.append(dict(id=0, name='Role %d' % i, selected=False))
                
            return dict(page='User roles', came_from=kw.get('came_from'),
                        user=dict(id=user.user_id, name=user.user_name), 
                        roles=roles)
            
        except Exception, e:
            logger.error(e)
        
    @expose('json')
    @require(predicates.has_any_permission('manage', 'users'))
    def update_role(self, **kw):

        logger = logging.getLogger('UsersController.roles')        
        try:
            id_user = get_paramw(kw, 'id_user', int)
            id_role = get_paramw(kw, 'id_role', int)
            selected = get_paramw(kw, 'selected', strtobool)
            
            if id_user == 1 and id_role == 1:
                raise Exception('It is not possible to remove "managers" privilege from "superuser"')
            
            user_role = dbs.query(SapnsUserRole).\
                filter(and_(SapnsUserRole.role_id == id_role,
                            SapnsUserRole.user_id == id_user,
                            )).\
                first()
                
            if selected:
                if not user_role:
                    user_role = SapnsUserRole()
                    user_role.role_id = id_role
                    user_role.user_id = id_user
                    
                    dbs.add(user_role)
                    dbs.flush()
                    
            else:
                if user_role:
                    user_role = dbs.query(SapnsUserRole).\
                        filter(and_(SapnsUserRole.role_id == id_role,
                                    SapnsUserRole.user_id == id_user,
                                    )).\
                        delete()
                        
                    dbs.flush()
                    
            return sj.dumps(dict(status=True))
        
        except Exception, e:
            logger.error(e)
            return sj.dumps(dict(status=False))
        
    @expose('json')
    def all(self):
        logger = logging.getLogger('Users.all')
        def _all():
            logger.info('Getting all users...')
            users = []
            for user in dbs.query(SapnsUser).order_by(SapnsUser.user_name):
                users.append(dict(id=user.user_id, display_name=user.display_name, 
                                  user_name=user.user_name))
                
            return users
                
        _cache = cache.get_cache('users_all')
                        
        return dict(users=_cache.get_value(key='all', createfunc=_all, expiretime=3600))