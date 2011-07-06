# -*- coding: utf-8 -*-
"""Users management controller"""

# turbogears imports
from tg import expose, url, config, redirect, require

# third party imports
from pylons.i18n import ugettext as _
from pylons.i18n import lazy_ugettext as l_
from repoze.what import authorize, predicates

# project specific imports
from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs

import logging
from sapns.model.sapnsmodel import SapnsUser 
from neptuno.dataset import DataSet

__all__ = ['UsersControllers']

class UsersController(BaseController):
    
    allow_only = authorize.not_anonymous()
    
    @expose('sapns/users/index.html')
    @require(predicates.has_any_permission('manage', 'users'))
    def index(self, came_from='/dashboard'):
    
        pos = 0

        ds = DataSet([('id', 'id',  ''), 
                      ('display_name', _('Display name'), ''), 
                      ('user_name', _('User name'), ''),
                      ('e_mail', _('E-mail address'), ''),
                      ])
        
        for us in dbs.query(SapnsUser).order_by(SapnsUser.user_id):
            ds.append(dict(id=us.user_id,
                           display_name=us.display_name, 
                           user_name=us.user_name,
                           e_mail=us.email_address,
                           ))
            
        actions = []
        actions.append(dict(title=_('New'), url='/dashboard/users/new', require_id=False))
        actions.append(dict(title=_('Edit'), url='/dashboard/users/edit', require_id=True))
        actions.append(dict(title=_('Delete'), url='/dashboard/users/delete', require_id=True))
        
        # Reading global settings
        ds.date_fmt = config.get('formats.date', default='%m/%d/%Y')
        ds.time_fmt = config.get('formats.time', default='%H:%M')
        ds.true_const = _('Yes')
        ds.false_const = _('No')
        
        #ds.float_fmt = app_cfg.format_float
        
        data = ds.to_data()
        
        cols = []
        for col in ds.labels:
            w = 120
            if col == 'id':
                w = 60
                
            cols.append(dict(title=col,
                             width=w,
                             align='center'))

        # rows in this page
        totalp = ds.count - pos
        
        return dict(page='users',
                    show_ids=True,
                    came_from=url(came_from),
                    link=None,
                    grid=dict(caption=None, name='users_list',
                              cls='', 
                              search_url=url('/dashboard/users'), 
                              cols=cols, data=data, 
                              actions=actions, pag_n=1, rp=0, pos=0,
                              totalp=totalp, total=ds.count, total_pag=1))
        
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
            
        
    
    @expose()
    @require(predicates.has_any_permission('manage', 'users'))
    def delete(self, **params):
        
        came_from = params.get('came_from')
        if came_from:
            came_from = url(came_from)
        
        user_name = ''
        logger = logging.getLogger(__name__ + '/delete')
        try:
            id = int(params['id'])
            
            user = dbs.query(SapnsUser).get(id)
            user_name = user.display_name
            
            dbs.query(SapnsUser).\
                filter(SapnsUser.user_id == id).\
                delete()
                
            dbs.flush()

        except Exception, e:
            logger.error(e)
            redirect(url('/message', 
                         params=dict(message=unicode(e), came_from='')))
        
        if came_from:
            redirect(came_from)
            
        else:
            redirect(url('/message', params=dict(message='User "%s" was successfully deleted' % user_name,
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
        users = []
        for user in dbs.query(SapnsUser).order_by(SapnsUser.user_name):
            users.append(dict(id=user.user_id, display_name=user.display_name, 
                              user_name=user.user_name))
            
        return dict(users=users)