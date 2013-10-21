# -*- coding: utf-8 -*-

from neptuno.util import get_paramw
from pylons.i18n import ugettext as _
from repoze.what import authorize #, predicates
from sapns.lib.base import BaseController
from sapns.lib.sapns.util import add_language
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser, SapnsPermission, SapnsShortcut
from sqlalchemy.sql.expression import and_
from tg import expose, request, cache
import logging
import simplejson as sj

__all__ = ['PermissionsController']

class EPermissions(Exception):
    pass

class PermissionsController(BaseController):
    
    allow_only = authorize.in_group('managers')
    
    @expose('sapns/permissions/create_shortcuts.html')
    @add_language
    def create_shortcuts(self, permission_id, **kw):
        
        permission = dbs.query(SapnsPermission).get(permission_id)
        
        return dict(page=_(u'Create shortcuts from permissions'),
                    came_from=kw.get('came_from'),
                    permission=dict(id=permission.permission_id,
                                    title=permission.display_name,
                                    name=permission.permission_name,
                                    ),
                    )
        
    @expose('sapns/permissions/user_groups.html')
    def user_groups(self, user_id):
        
        user = dbs.query(SapnsUser).get(int(user_id))
        
        def _children_shortcuts(parent_id):
            sc_groups = []
            for sc in dbs.query(SapnsShortcut).\
                    filter(and_(SapnsShortcut.user_id == user.user_id,
                                SapnsShortcut.parent_id == parent_id,
                                SapnsShortcut.permission_id == None,
                                )).\
                    order_by(SapnsShortcut.order):
            
                sc_groups.append(dict(id=sc.shortcut_id, title=sc.title,
                                      children=_children_shortcuts(sc.shortcut_id)))
                
            return sc_groups
        
        db = user.get_dashboard()
        sc_groups = [dict(id=db.shortcut_id,
                          title=db.title,
                          children=_children_shortcuts(db.shortcut_id),
                          )]
        
        return dict(sc_groups=sc_groups)
    
    @expose('json')
    def create_shortcut_(self, **kw):
        
        logger = logging.getLogger('PermissionsController.create_shortcut_')
        try:
            user_id = get_paramw(kw, 'user_id', int)
            permission_id = get_paramw(kw, 'permission_id', int)
            groups = get_paramw(kw, 'groups', sj.loads)
            
            p = dbs.query(SapnsPermission).get(permission_id)
            
            if p.type not in [SapnsPermission.TYPE_LIST, SapnsPermission.TYPE_PROCESS] or \
            p.type == SapnsPermission.TYPE_PROCESS and p.requires_id:
                raise EPermissions(_(u'Shortcuts can only be created from LIST and PROCESS (no required id) type permissions'))
            
            title = p.display_name
            if p.type == SapnsPermission.TYPE_LIST:
                title = p.class_.title
            
            for id_group in groups:
                
                group = dbs.query(SapnsShortcut).get(id_group)
                
                sc = SapnsShortcut()
                sc.user_id = user_id
                sc.parent_id = id_group
                sc.permission_id = permission_id
                sc.title = title
                sc.order = group.next_order()
                dbs.add(sc)
                dbs.flush()
                
                _key = '%d_%d' % (user_id, id_group)
                cache.get_cache('user_get_shortcuts').remove_value(key=_key)
            
            return dict(status=True)
        
        except EPermissions, e:
            logger.error(e)
            return dict(status=False, msg=unicode(e))
            
        except Exception, e:
            logger.error(e)
            return dict(status=False)