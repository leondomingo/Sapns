# -*- coding: utf-8 -*-

from neptuno.dict import Dict
from neptuno.util import get_paramw, strtobool
from pylons import cache
from pylons.i18n import ugettext as _
from repoze.what import authorize #, predicates
from sapns.lib.base import BaseController
from sapns.lib.sapns.util import add_language
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser, SapnsClass, SapnsRole, \
    SapnsAttrPrivilege, SapnsPermission, SapnsShortcut
from sqlalchemy.sql.expression import and_
from tg import expose, request
import logging
import simplejson as sj

__all__ = ['PermissionsController']

class PermissionsController(BaseController):
    
    allow_only = authorize.in_group('managers')
    
    @expose('sapns/permissions/create_shortcuts.html')
    @add_language
    def create_shortcuts(self, permission_id, **kw):
        
        permission = dbs.query(SapnsPermission).get(permission_id)
        
        users = []
        for user in dbs.query(SapnsUser).\
                order_by(SapnsUser.user_id):
            
            roles = [r.group_name for r in user.roles]
            
            users.append(dict(id=user.user_id,
                              display_name=user.display_name,
                              selected=user.user_id == request.identity['user'].user_id,
                              roles=','.join(roles),
                              ))
        
        return dict(permission=dict(id=permission.permission_id,
                                    title=permission.display_name,
                                    name=permission.permission_name,
                                    ),
                    users=users,
                    page=_(u'Create shortcuts from permissions'),
                    came_from=kw.get('came_from'))
        
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
            
            title = p.display_name
            if p.type in [SapnsPermission.TYPE_NEW, SapnsPermission.TYPE_EDIT, 
                          SapnsPermission.TYPE_DOCS, SapnsPermission.TYPE_DOCS]:
                title = u'%s:%s' % (p.class_.title, p.display_name)
                
            elif p.type == SapnsPermission.TYPE_LIST:
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
            
            return dict(status=True)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)