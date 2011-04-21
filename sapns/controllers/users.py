# -*- coding: utf-8 -*-
"""Users management controller"""

# turbogears imports
from tg import expose, url, config, redirect

# third party imports
from pylons.i18n import ugettext as _
from repoze.what import authorize

# project specific imports
from sapns.lib.base import BaseController
from sapns.model import DBSession

import logging
from sapns.model.sapnsmodel import SapnsUser 
from neptuno.dataset import DataSet
from sapns.controllers.util import UtilController

class UsersController(BaseController):
    # only for "managers"
    allow_only = authorize.has_permission('manage') or authorize.has_permission('users')
    
    @expose('users/index.html')
    def index(self, came_from='/users'):
    
        pos = 0

        ds = DataSet([('id', 'id',  ''), 
                      ('display_name', _('Display name'), ''), 
                      ('user_name', _('User name'), ''),
                      ('e_mail', _('E-mail address'), ''),
                      ])
        
        for us in DBSession.query(SapnsUser).order_by(SapnsUser.user_id):
            ds.append(dict(id=us.user_id,
                           display_name=us.display_name, 
                           user_name=us.user_name,
                           e_mail=us.email_address,
                           ))
            
        actions = []
        actions.append(dict(title=_('New'), url='/users/user_new', require_id=False))
        actions.append(dict(title=_('Edit'), url='/users/user_edit', require_id=True))
        actions.append(dict(title=_('Delete'), url='/users/user_delete', require_id=True))
        
        # Reading global settings
        ds.date_fmt = config.get('grid.date_format', default='%m/%d/%Y')
        ds.time_fmt = config.get('grid.time_format', default='%H:%M')
        ds.true_const = config.get('grid.true_const', default='Yes')
        ds.false_const = config.get('grid.false_const', default='No')
        
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
                              search_url=url('/users'), 
                              cols=cols, data=data, 
                              actions=actions, pag_n=1, rp=0, pos=0,
                              totalp=totalp, total=ds.count, total_pag=1))
        
    @expose('users/user_edit.html')
    def user_edit(self, id=None, cls=None, came_from='/users'):
        
        user = DBSession.query(SapnsUser).get(id)
        return dict(user=user, came_from=url(came_from))
    
    @expose('users/user_edit.html')
    def user_new(self, id=None, cls=None, came_from='/users'):
        
        other_users = []
        for us in DBSession.query(SapnsUser):
            other_users.append(dict(id=us.user_id, name=us.user_name))
        
        return dict(user={}, other_users=other_users, came_from=url(came_from))
    
    @expose()
    def user_save(self, **params):
        
        try:
            new_user = False
            if params['id']:
                user = DBSession.query(SapnsUser).get(params['id'])
            else:
                new_user = True
                user = SapnsUser()
                
            user.display_name = params['display_name']
            user.user_name = params['user_name']
            user.email_address = params['email_address']
            
            if params['password'] != '':
                user.password = params['password']
                
            DBSession.add(user)
            DBSession.flush()
            
            # TODO: copy shortcuts form another user
            if new_user:
                user.copy_from(int(params['copy_from']))
        
        except:
            redirect(url('/message', 
                         dict(message=_('An error occurred while saving the user'),
                              came_from='/users')))

        redirect(url('/users'))
    
    @expose('users/user_delete.html')
    def user_delete(self, id=None, cls=None, came_from='/users'):
        return dict(came_from=url(came_from))
    
    @expose('users/permission.html')
    def permission(self, came_from='/users'):
        return dict(came_from=url(came_from))
    
    @expose('users/roles.html')
    def roles(self, came_from='/users'):
        return dict(came_from=url(came_from))
        