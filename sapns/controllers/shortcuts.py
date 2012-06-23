# -*- coding: utf-8 -*-
"""Shortcuts management controller"""

from pylons import cache
from pylons.i18n import ugettext as _
from repoze.what import authorize, predicates as p_
from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser, SapnsShortcut, SapnsClass,\
    SapnsPermission
from tg import expose, url, redirect, request, require
import logging
from neptuno.util import get_paramw
import simplejson as sj

__all__ = ['ShortcutsController']

class ShortcutsController(BaseController):
    
    allow_only = authorize.not_anonymous()
    
    @expose('sapns/shortcuts/edit.html')
    @require(p_.not_anonymous())
    def edit(self, id=None, **params):
        came_from = params.get('came_from', '/')
        page = _('Shorcuts editing')
        
        return dict(page=page, came_from=came_from)
    
    @expose()
    @require(p_.not_anonymous())
    def save(self, id=None, **params):
        came_from = params.get('came_from', '/')
        redirect(url(came_from))
    
    @expose('json')
    @require(p_.not_anonymous())
    def delete(self, id_shortcut, **params):
        
        logger = logging.getLogger('ShortcutsController.delete')
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
    @require(p_.not_anonymous())
    def bookmark(self, id_shortcut, **params):
        logger = logging.getLogger(__name__ + '/bookmark')
        try:
            logger.info('Bookmarking shortcut [%s]' % id_shortcut)
            user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
            
            dboard = user.get_dashboard()
            sc = dboard.add_child(id_shortcut)
            
            _key = '%d_%d' % (user.user_id, dboard.shortcut_id)
            cache.get_cache('user_get_shortcuts').remove_value(key=_key)
            
            logger.info(sc.permission.permission_name)

            return dict(status=True, shortcut=dict(id=sc.shortcut_id,
                                                   title=sc.title,
                                                   url=sc.permission.url,
                                                   ))
            
            return dict(status=True)
            
        except Exception, e:
            logger.error(e)
            return dict(status=False) #, message=str(e).decode('utf-8'))
        
    @expose('json')
    @require(p_.not_anonymous())
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
    @require(p_.not_anonymous())
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
    @require(p_.not_anonymous())
    def reorder(self, **kw):
        
        logger = logging.getLogger('ShortcutsController.reorder')
        try:
            user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
            order = get_paramw(kw, 'order', sj.loads)
            i = 0
            for id_shortcut in order:
                sc = dbs.query(SapnsShortcut).get(id_shortcut)
                #sc = SapnsShortcut()
                sc.order = i
                dbs.add(sc)
                dbs.flush()
                
                i += 1
                
            key_ = '%d_%d' % (user.user_id, user.get_dashboard().shortcut_id)
            cache.get_cache('user_get_shortcuts').remove_value(key=key_)
            
            return dict(status=True)
            
        except Exception, e:
            logger.error(e)
            return dict(status=False)
        
    @expose('json')
    @require(p_.not_anonymous())
    def bookmark_(self, **kw):
        
        logger = logging.getLogger('ShortcutsController.add_to_sidebar')
        try:
            cls = get_paramw(kw, 'cls', str)
            
            class_ = SapnsClass.by_name(cls)
            user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
            
            db = user.get_dashboard()
            
            p_name = u'%s#list' % cls
            p = dbs.query(SapnsPermission).\
                filter(SapnsPermission.permission_name == p_name).\
                first()
            
            sc = SapnsShortcut()
            sc.title = class_.title
            sc.user_id = user.user_id
            sc.permission_id = p.permission_id
            sc.parent_id = db.shortcut_id
            sc.order = db.next_order()
            
            dbs.add(sc)
            dbs.flush()
            
            user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
            key_ = '%d_%d' % (user.user_id, user.get_dashboard().shortcut_id)
            cache.get_cache('user_get_shortcuts').remove_value(key=key_)
            
            return dict(status=True, shortcut=dict(id=sc.shortcut_id,
                                                   title=class_.title,
                                                   url=url('/dashboard/list/%s?came_from=' % cls),
                                                   ))
            
        except Exception, e:
            logger.error(e)
            return dict(status=False)