# -*- coding: utf-8 -*-
"""Shortcuts management controller"""

# turbogears imports
from tg import expose, url, config, redirect, request

# third party imports
from pylons.i18n import ugettext as _
from pylons.i18n import lazy_ugettext as l_
from repoze.what import authorize

# project specific imports
from sapns.lib.base import BaseController
from sapns.model import DBSession

import logging
from sapns.model.sapnsmodel import SapnsUser , SapnsShortcut
from neptuno.dataset import DataSet

__all__ = ['ShortcutsController']

class ShortcutsController(BaseController):
    
    allow_only = authorize.not_anonymous()
    
    @expose('shortcuts/edit.html')
    def edit(self, id=None, **params):
        came_from = params.get('came_from', '/')
        page = _('Shorcuts editing')
        
        return dict(page=page, came_from=came_from)
    
    @expose()
    def save(self, id=None, **params):
        came_from = params.get('came_from', '/')
        redirect(url(came_from))
    
    @expose('json')
    def delete(self, id=None, **params):
        
        logger = logging.getLogger(__name__ + '/delete')
        try:
            logger.info('Deleting shortcut [%s]' % id)
            
            DBSession.query(SapnsShortcut).\
                filter(SapnsShortcut.shortcut_id == id).\
                delete()
            
            DBSession.flush()
        
            return dict(status=True)
    
        except Exception, e:
            logger.error(e)
            return dict(status=False)
    
    @expose('json')
    def bookmark(self, id=None, **params):
        logger = logging.getLogger(__name__ + '/bookmark')
        try:
            logger.info('Bookmarking shortcut [%s]' % id)
            user = DBSession.query(SapnsUser).get(request.identity['user'].user_id)
            user.get_dashboard().add_child(id)
            
            return dict(status=True)
            
        except Exception, e:
            logger.error(e)
            return dict(status=False)
        
    @expose('json')
    def share(self, id_sc=None, id_user=None, **params):
        
        logger = logging.getLogger(__name__ + '/share')
        try:
            logger.info('Sharing shortcut [%s]' % id)
            
            user = DBSession.query(SapnsUser).get(id_user)
            if not user:
                raise Exception('User [%s] does not exist' % id_user)
            
            user.get_dashboard().add_child(id_sc)            
            
            return dict(status=True)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False) 
        
        