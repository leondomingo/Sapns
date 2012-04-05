# -*- coding: utf-8 -*-
"""Shortcuts management controller"""

from pylons import cache
from pylons.i18n import ugettext as _
from repoze.what import authorize, predicates
from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser, SapnsShortcut
from tg import expose, url, redirect, request, require
import logging

__all__ = ['ShortcutsController']

class ShortcutsController(BaseController):
    
    allow_only = authorize.not_anonymous()
    
    @expose('sapns/shortcuts/edit.html')
    @require(predicates.not_anonymous())
    def edit(self, id=None, **params):
        came_from = params.get('came_from', '/')
        page = _('Shorcuts editing')
        
        return dict(page=page, came_from=came_from)
    
    @expose()
    @require(predicates.not_anonymous())
    def save(self, id=None, **params):
        came_from = params.get('came_from', '/')
        redirect(url(came_from))
    
    @expose('json')
    @require(predicates.not_anonymous())
    def delete(self, id_shortcut, **params):
        
        logger = logging.getLogger(__name__ + '/delete')
        try:
            logger.info('Deleting shortcut [%s]' % id_shortcut)
            
            # the shortcut to be deleted
            sc = dbs.query(SapnsShortcut).get(id_shortcut)
            
            dbs.query(SapnsShortcut).\
                filter(SapnsShortcut.shortcut_id == id_shortcut).\
                delete()
            
            dbs.flush()
             
            _key = '%d_%d' % (sc.user_id, sc.parent_id)
            cache.get_cache('user_get_shortcuts').remove_value(key=_key)
        
            return dict(status=True)
    
        except Exception, e:
            logger.error(e)
            return dict(status=False)
    
    @expose('json')
    @require(predicates.not_anonymous())
    def bookmark(self, id_shortcut, **params):
        logger = logging.getLogger(__name__ + '/bookmark')
        try:
            logger.info('Bookmarking shortcut [%s]' % id_shortcut)
            user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
            
            dboard = user.get_dashboard()
            dboard.add_child(id_shortcut)
            
            _key = '%d_%d' % (user.user_id, dboard.shortcut_id)
            cache.get_cache('user_get_shortcuts').remove_value(key=_key)
            
            return dict(status=True)
            
        except Exception, e:
            logger.error(e)
            return dict(status=False) #, message=str(e).decode('utf-8'))
        
    @expose('json')
    @require(predicates.not_anonymous())
    def from_list(self, title, link):
        logger = logging.getLogger('shortcuts/from_list')
        try:
            # connected user
            user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
            user.from_list(title, link)

            return dict(status=True)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=unicode(e))
        
    @expose('json')
    @require(predicates.not_anonymous())
    def share(self, id_sc=None, id_user=None, **params):
        
        logger = logging.getLogger(__name__ + '/share')
        try:
            logger.info('Sharing shortcut [%s]' % id)
            
            user = dbs.query(SapnsUser).get(id_user)
            if not user:
                raise Exception('User [%s] does not exist' % id_user)
            
            user.get_dashboard().add_child(id_sc)            
            
            return dict(status=True)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)
        
    @expose('json')
    def reorder(self, id_sc, type_):
        
        logger = logging.getLogger('ShortcutsController.reorder')
        try:
            sc = dbs.query(SapnsShortcut).get(id_sc)            
            logger.info('Reordering shortcut (%s %s)' % (sc, type))
            
            sc.reorder(type_)
            
            return dict(status=True)
            
        except Exception, e:
            logger.error(e)
            return dict(status=False)
        
        