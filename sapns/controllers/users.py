# -*- coding: utf-8 -*-
"""Users management controller"""

from neptuno.util import get_paramw, strtobool
from pylons import cache
from pylons.i18n import ugettext as _
from sapns.lib.base import BaseController
from sapns.lib.sapns.util import add_language, log_access
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser, SapnsRole, SapnsUserRole
from sqlalchemy.sql.expression import and_
from tg import expose, url, redirect, require, request, predicates as p_
import logging
import simplejson as sj
from webob.exc import HTTPForbidden

__all__ = ['UsersController']

class EUser(Exception):
    pass

class UsersController(BaseController):
    
    allow_only = p_.not_anonymous()
    
    @expose('sapns/users/edit/edit.html')
    @require(p_.not_anonymous())
    @add_language
    @log_access('edit user')
    def edit(self, cls, id_, **params):

        id_user = int(id_)
        
        is_manager = u'managers' in request.identity['groups']
        
        if request.identity['user'].user_id != id_user and not is_manager:
            raise HTTPForbidden()
        
        user = dbs.query(SapnsUser).get(id_user)
        return dict(user=user, came_from=params.get('came_from'))
    
    @expose('sapns/users/edit/edit.html')
    @require(p_.has_any_permission('manage', 'users'))
    @log_access('new user')
    def new(self, cls, **params):
        came_from = params.get('came_from', '/dashboard/users')
        return dict(user={}, came_from=url(came_from))
    
    @expose('json')
    @require(p_.not_anonymous())
    @log_access('save user')
    def save(self, **params):
        
        logger = logging.getLogger('UsersController.save')
        try:
            id_ = get_paramw(params, 'id', int, opcional=True)

            is_manager = u'managers' in request.identity['groups']
            if request.identity['user'].user_id != id_ and not is_manager:
                raise HTTPForbidden()

            display_name = get_paramw(params, 'display_name', unicode)
            user_name = get_paramw(params, 'user_name', unicode)
            email_address = get_paramw(params, 'email_address', unicode)
            password = get_paramw(params, 'password', unicode, opcional=True)
            copy_from = get_paramw(params, 'copy_from', int, opcional=True)
            
            new_user = False
            if id_:
                user = dbs.query(SapnsUser).get(id_)
            else:
                new_user = True
                user = SapnsUser()
                
            user.display_name = display_name

            # user_name            
            another = dbs.query(SapnsUser).\
                filter(and_(SapnsUser.user_id != user.user_id,
                            SapnsUser.user_name == user_name,
                            )).\
                first()
            if another:
                raise EUser(_('"User name" is already in use'))

            # email_address            
            another = dbs.query(SapnsUser).\
                filter(and_(SapnsUser.user_id != user.user_id,
                            SapnsUser.email_address == email_address,
                            )).\
                first()
                
            if another:
                raise EUser(_('"E-mail address" is already in use'))
            
            # user_name
            user.user_name = user_name
            
            # email_address
            user.email_address = email_address
            
            if password:
                user.password = password
                
            dbs.add(user)
            dbs.flush()
            
            # copy shortcuts and privileges form another user
            if new_user:
                user.copy_from(copy_from)
                
            return dict(status=True)
        
        except EUser, e:
            logger.error(e)
            return dict(status=False, message=unicode(e))
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)

    @expose('sapns/users/permission.html')
    @require(p_.has_any_permission('manage', 'users'))
    def permission(self, came_from='/dashboard/users'):
        return dict(came_from=url(came_from))
    
    @expose('sapns/users/roles.html')
    @require(p_.has_any_permission('manage', 'users'))
    @add_language
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
                
            return dict(page='User roles', came_from=kw.get('came_from'),
                        user=dict(id=user.user_id, name=user.user_name), 
                        roles=roles)
            
        except Exception, e:
            logger.error(e)
        
    @expose('json')
    @require(p_.has_any_permission('manage', 'users'))
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
    def all_(self):
        #logger = logging.getLogger('Users.all')
        def _all():
            #logger.info('Getting all users...')
            users = []
            for user in dbs.query(SapnsUser).order_by(SapnsUser.user_id):
                users.append(dict(id=user.user_id, display_name=user.display_name, 
                                  user_name=user.user_name))
                
            return users
                
        _cache = cache.get_cache('users_all')
                        
        return dict(users=_cache.get_value(key='all', createfunc=_all, expiretime=0))
    
    @expose('sapns/users/dashboard/dashboard.html')
    @require(p_.in_group(u'managers'))
    @log_access('user dashboard')
    def dashboard(self, user_id, **kw):
        user_id = int(user_id)
        user = dbs.query(SapnsUser).get(user_id)
        
        return dict(page=u'[%s]' % user.display_name,
                    came_from=kw.get('came_from'), 
                    this_shortcut={}, user=dict(id=user_id, display_name=user.display_name),
                    _came_from=url(user.entry_point() or '/dashboard/?user_id=%d' % user_id))
