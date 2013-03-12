# -*- coding: utf-8 -*-
"""Shortcuts management controller"""

from neptuno.util import get_paramw
from pylons import cache
from pylons.i18n import lazy_ugettext as l_, ugettext as _
from sapns.lib.base import BaseController
from sapns.lib.sapns.util import ROLE_MANAGERS
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser, SapnsShortcut, SapnsClass, \
    SapnsPermission, SapnsPrivilege, SapnsRole
from sqlalchemy.sql.expression import and_, or_
from tg import expose, url, request, require, predicates as p_
import logging
import simplejson as sj

__all__ = ['ShortcutsController']

class ShortcutsController(BaseController):
    
    allow_only = p_.not_anonymous()
    
    @expose('sapns/shortcuts/inner_list.html')
    @require(p_.not_anonymous())
    def list_(self, **kw):
        id_user = get_paramw(kw, 'id_user', int)
        user = dbs.query(SapnsUser).get(id_user)
        
        sc_parent = get_paramw(kw, 'sc_parent', int, opcional=True)

        dashboard_ = user.get_dashboard().shortcut_id
        
        id_parent = sc_parent
        if not sc_parent or sc_parent == dashboard_:
            id_parent = dashboard_

        shortcuts = user.get_shortcuts(id_parent=id_parent)
        
        came_from = url('/dashboard/data_exploration/', params=dict(user_id=id_user, sc_parent=id_parent))        
        
        return dict(shortcuts=shortcuts, sc_parent=id_parent,
                    user_id=id_user, came_from=came_from)
    
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
    def bookmark(self, id_shortcut, **kw):
        logger = logging.getLogger('ShortcutsController.bookmark')
        try:
            logger.info('Bookmarking shortcut [%s]' % id_shortcut)
            
            # user
            user_id = get_paramw(kw, 'user_id', int, opcional=True)
            if not user_id:
                user_id = request.identity['user'].user_id
                
            user = dbs.query(SapnsUser).get(user_id)
            
            dboard = user.get_dashboard()
            sc = dboard.add_child(id_shortcut)
            
            _key = '%d_%d' % (user.user_id, dboard.shortcut_id)
            cache.get_cache('user_get_shortcuts').remove_value(key=_key)
            
            return dict(status=True, shortcut=dict(id=sc.shortcut_id,
                                                   title=sc.title,
                                                   url=sc.permission.url if sc.permission_id else '',
                                                   ))
            
            return dict(status=True)
            
        except Exception, e:
            logger.error(e)
            return dict(status=False) #, message=str(e).decode('utf-8'))
        
    @expose('json')
    @require(p_.not_anonymous())
    def move(self, **kw):
        logger = logging.getLogger('ShortcutsController.move')
        try:
            id_shortcut = get_paramw(kw, 'id_shortcut', int)
            id_group = get_paramw(kw, 'id_group', int)
            
            logger.info(u'Moving shortcut [%s] to [%d]' % (id_shortcut, id_group))
            user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
            
            group = dbs.query(SapnsShortcut).get(id_group)
            
            sc = dbs.query(SapnsShortcut).get(id_shortcut)
            #sc = SapnsShortcut()
            sc.parent_id = id_group
            sc.order = group.next_order()
            dbs.add(sc)
            dbs.flush()
            
            _key = '%d_%d' % (user.user_id, id_group)
            cache.get_cache('user_get_shortcuts').remove_value(key=_key)
            
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
        
    @expose('sapns/shortcuts/share/users.html')
    @require(p_.not_anonymous())
    def share_users(self, **kw):
        
        shortcut_id = get_paramw(kw, 'shortcut_id', int)
        shortcut = dbs.query(SapnsShortcut).get(shortcut_id)
        
        return dict(shortcut=dict(id=shortcut.shortcut_id,
                                  title=shortcut.title,
                                  ))
        
    @expose('sapns/shortcuts/share/roles.html')
    @require(p_.not_anonymous())
    def share_roles(self, **kw):
        
        shortcut_id = get_paramw(kw, 'shortcut_id', int)
        shortcut = dbs.query(SapnsShortcut).get(shortcut_id)
        
        return dict(shortcut=dict(id=shortcut.shortcut_id,
                                  title=shortcut.title,
                                  ))        
        
    @expose('json')
    @require(p_.not_anonymous())
    def share(self, **kw):
        logger = logging.getLogger('ShortcutsController.share')
        try:
            shortcut_id = get_paramw(kw, 'shortcut_id', int)
            shortcut = dbs.query(SapnsShortcut).get(shortcut_id)
            
            this_user = request.identity['user'].user_id
            
            # only "managers" are allowed to share other users' shortcuts
            if ROLE_MANAGERS not in request.identity['groups'] and this_user != shortcut.user_id:
                raise Exception(_(u'You are not the owner of this shortcut'))
            
            users = get_paramw(kw, 'users', sj.loads, opcional=True)
            if not users:
                roles = get_paramw(kw, 'roles', sj.loads)
            
            logger.info('Sharing shortcut [%s]' % shortcut_id)
            
            if users:
                for user_id in users:
                    if user_id != this_user:
                        try:
                            user = dbs.query(SapnsUser).get(user_id)
                            user.get_dashboard().add_child(shortcut_id)
                            
                        except Exception, e:
                            logger.error(e)
                        
            elif roles:
                # sharing a shortcut with a role means sharing with all the users in that role
                for role_id in roles:
                    role = dbs.query(SapnsRole).get(role_id)
                    for user in role.users_:
                        if user.user_id != this_user:
                            try:
                                user = dbs.query(SapnsUser).get(user.user_id)
                                user.get_dashboard().add_child(shortcut_id)
                                
                            except Exception, e:
                                logger.error(e)
            
            return dict(status=True)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)
        
    @expose('json')
    @require(p_.not_anonymous())
    def reorder(self, **kw):
        
        logger = logging.getLogger('ShortcutsController.reorder')
        try:
            # user
            user_id = get_paramw(kw, 'user_id', int, opcional=True)
            if not user_id:
                user_id = request.identity['user'].user_id
            
            user = dbs.query(SapnsUser).get(user_id)
            
            # reorder shortcuts
            order = get_paramw(kw, 'order', sj.loads)
            i = 0
            for id_shortcut in order:
                sc = dbs.query(SapnsShortcut).get(id_shortcut)
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
            
            # user
            user_id = get_paramw(kw, 'user_id', int, opcional=True)
            if not user_id:
                user_id = request.identity['user'].user_id
                
            user = dbs.query(SapnsUser).get(user_id)
            
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
        
    @expose('sapns/shortcuts/new.html')
    @require(p_.not_anonymous())
    def edit(self, **kw):
        
        # user
        user_id = get_paramw(kw, 'user_id', int, opcional=True)
        if not user_id:
            user_id = request.identity['user'].user_id
            
        user = dbs.query(SapnsUser).get(user_id)
        
        # roles (of this user)
        roles = set([r.group_name for r in user.roles])        
        
        id_shortcut = get_paramw(kw, 'id_shortcut', int, opcional=True)
        id_parent = get_paramw(kw, 'id_parent', int, opcional=True)
        if not id_parent:
            id_parent = user.get_dashboard().shortcut_id
        
        shortcut = dict(id_shortcut=id_shortcut,
                        id_parent=id_parent,
                        id_user=user_id)
        
        classes = []
        
        if id_shortcut:
            # edit
            sc = dbs.query(SapnsShortcut).get(id_shortcut)
            shortcut.update(title=sc.title)
            
        else:
            # new
            for cls in dbs.query(SapnsClass).order_by(SapnsClass.title):
                
                if u'managers' not in roles and not SapnsPrivilege.has_privilege(user_id, cls.class_id):
                    continue
                
                cls_ = dict(id=cls.class_id,
                            title=cls.title,
                            name=cls.name,
                            is_view=cls.parent_class_id != None)
                                
                classes.append(cls_)
                
            # permissions with no associated class
            classes.append(dict(id=-1,
                                title='*',
                                name=None,
                                ))
        
        return dict(shortcut=shortcut, classes=classes)
    
    @expose('sapns/shortcuts/permissions.html')
    @require(p_.not_anonymous())
    def class_permissions(self, **kw):
        class_id = get_paramw(kw, 'class_id', int)
        if class_id == -1:
            cond_class = SapnsPermission.class_id == None
            
        else:
            cond_class = SapnsPermission.class_id == class_id
        
        roles = request.identity['groups']
        user_id = request.identity['user'].user_id
        user = dbs.query(SapnsUser).get(user_id)
        
        permissions = []
        for p in dbs.query(SapnsPermission).\
                filter(and_(cond_class,
                            or_(SapnsPermission.type == SapnsPermission.TYPE_LIST,
                                and_(SapnsPermission.type == SapnsPermission.TYPE_PROCESS,
                                     SapnsPermission.url != None,
                                     SapnsPermission.requires_id == False,
                                     )
                                )
                            )):
            
            if u'managers' not in roles and not user.has_permission(p.permission_name):
                continue
            
            title = p.display_name
            if p.type == SapnsPermission.TYPE_LIST:
                if p.class_.parent_class_id is None:
                    title = u'[%s]' % l_(u'Table')
                else:
                    title = u'[%s]' % l_(u'View')
            
            elif p.type == SapnsPermission.TYPE_PROCESS:
                pass
            
            permissions.append(dict(id=p.permission_id,
                                    title=title,
                                    name=p.permission_name,
                                    ))
                
        return dict(permissions=permissions)
    
    @expose('json')
    @require(p_.not_anonymous())
    def save(self, **kw):
        logger = logging.getLogger('ShortcutsController.save')
        try:
            id_shortcut = get_paramw(kw, 'id_shortcut', int, opcional=True)
            title = get_paramw(kw, 'title', unicode)
            id_user = get_paramw(kw, 'id_user', int)
            id_parent = get_paramw(kw, 'id_parent', int, opcional=True)
            permissions = get_paramw(kw, 'permissions', sj.loads)
            
            user = dbs.query(SapnsUser).get(id_user)
            
            if not id_parent:
                # dashboard
                id_parent = user.get_dashboard().shortcut_id
            
            if not id_shortcut:
                sc_parent = dbs.query(SapnsShortcut).get(id_parent)
                
                if len(permissions) > 0:
                    # create several shortcuts
                    for permission_id in permissions:
                        
                        permission = dbs.query(SapnsPermission).get(permission_id)
                        
                        sc = SapnsShortcut()
                        sc.parent_id = id_parent
                        sc.user_id = id_user
                        sc.permission_id = permission_id
                        
                        # title
                        if permission.type == SapnsPermission.TYPE_PROCESS:
                            sc.title = permission.display_name
                            
                        elif permission.type == SapnsPermission.TYPE_LIST:
                            sc.title = permission.class_.title
                        
                        dbs.add(sc)
                        dbs.flush()
                        
                        sc_parent.add_child(sc.shortcut_id, copy=False)
                
                else:
                    # create a group
                    sc = SapnsShortcut()
                    sc.parent_id = id_parent
                    sc.user_id = id_user
                    sc.title = title
                    dbs.add(sc)
                    dbs.flush()
                    
                    sc_parent.add_child(sc.shortcut_id, copy=False)
                    
            else:
                sc = dbs.query(SapnsShortcut).get(id_shortcut)
                sc.title = title
                dbs.add(sc)
                dbs.flush()
                
            # reset cache
            key_ = '%d_%d' % (id_user, id_parent)
            cache.get_cache('user_get_shortcuts').remove_value(key=key_)
            
            return dict(status=True)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)