# -*- coding: utf-8 -*-
"""Users management controller"""

# turbogears imports
from tg import expose, url, response, config
from tg.i18n import set_lang

# third party imports
from pylons.i18n import ugettext as _
from repoze.what import authorize

# project specific imports
from sapns.lib.base import BaseController
from sapns.model import DBSession

import logging
from sqlalchemy.schema import MetaData
from sqlalchemy.sql.expression import and_
from sqlalchemy.types import INTEGER, NUMERIC, BIGINT, DATE, TEXT, VARCHAR,\
    BOOLEAN, BLOB
from sqlalchemy.dialects.postgresql.base import TIME, TIMESTAMP, BYTEA
from pylons.templating import render_jinja2
from sapns.model.sapnsmodel import SapnsClass, SapnsAttribute, SapnsUser,\
    SapnsShortcut, SapnsAction, SapnsPrivilege, SapnsAttrPrivilege
from neptuno.dataset import DataSet

class UsersController(BaseController):
    # only for "managers"
    allow_only = authorize.has_permission('manage')
    
    @expose('users/index.html')
    def index(self, came_from='/'):
    
        pos = 0

        ds = DataSet([('id', 'id',  ''), ('display_name', 'Display name', ''), 
                      ('user_name', 'User name', '')])
        
        for us in DBSession.query(SapnsUser).all():
            ds.append(dict(id=us.user_id,
                           display_name=us.display_name, 
                           user_name=us.user_name))
            
        actions = []
        actions.append(dict(title=_('New'), url='/users/user_new', require_id=True))
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
                    link=url(came_from),
                    grid=dict(caption=None, name='users_list',
                              cls='', 
                              search_url=url('/users'), 
                              cols=cols, data=data, 
                              actions=actions, pag_n=1, rp=0, pos=0,
                              totalp=totalp, total=ds.count, total_pag=1))
        
    @expose('users/user_edit.html')
    def user_edit(self, id=None, cls=None, link='/'):
        return dict(link=url(link))
    
    @expose('users/user_delete.html')
    def user_delete(self, id=None, cls=None, came_from='/'):
        return dict(came_from=url(came_from))
    
    @expose('users/permission.html')
    def permission(self, came_from='/'):
        return dict(came_from=url(came_from))
    
    @expose('users/roles.html')
    def roles(self, came_from='/'):
        return dict(came_from=url(came_from))
        