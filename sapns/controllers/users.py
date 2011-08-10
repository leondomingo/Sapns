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
from sapns.model.sapnsmodel import SapnsUser 
from neptuno.dataset import DataSet
from neptuno.util import get_paramw
from neptuno.postgres.search import search
from urllib import urlencode

__all__ = ['UsersControllers']

class UsersController(BaseController):
    
    allow_only = authorize.not_anonymous()
    
    @expose('sapns/users/edit.html')
    @require(predicates.not_anonymous())
    def edit(self, id, **params):
        
        id_user = int(id)
        
        came_from = params.get('came_from')
        if came_from:
            came_from = url(came_from)
        
        user = dbs.query(SapnsUser).get(id_user)
        return dict(user=user, came_from=came_from)
    
    @expose('sapns/users/edit.html')
    @require(predicates.has_any_permission('manage', 'users'))
    def new(self, **params):
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
    def roles(self, came_from='/dashboard/users'):
        return dict(came_from=url(came_from))
        
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