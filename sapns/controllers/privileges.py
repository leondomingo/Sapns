# -*- coding: utf-8 -*-
"""Privilege management controller"""

from neptuno.dict import Dict
from neptuno.util import get_paramw, strtobool
from pylons import cache
from pylons.i18n import ugettext as _
from repoze.what import authorize #, predicates
from sapns.lib.base import BaseController
from sapns.lib.sapns.util import init_lang, get_languages
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser, SapnsClass, SapnsRole, \
    SapnsAttrPrivilege, SapnsPermission
from sqlalchemy.sql.expression import and_
from tg import expose, url, redirect
import logging
import simplejson as sj

__all__ = ['PrivilegesController']

class PrivilegesController(BaseController):
    
    allow_only = authorize.in_group('managers')
    
    @expose('sapns/privileges/index.html')
    def index(self, **kw):
        
        logger = logging.getLogger('PrivilegesController.index')
        try:
            id_role = get_paramw(kw, 'id_role', int, opcional=True)
            id_user = get_paramw(kw, 'id_user', int, opcional=True)
            
            role = dbs.query(SapnsRole).get(id_role)
            
            came_from = kw.get('came_from', '/')
            page = _('Privilege management for "%s"') % role.group_name 
            
            return dict(page=page, id_role=id_role, id_user=id_user, 
                        came_from=came_from, lang=init_lang(),
                        languages=get_languages())
        
        except Exception, e:
            logger.error(e)
    
    @expose()
    def roles(self, id_role, **kw):
        kw.update(id_role=id_role)
        redirect(url('/dashboard/privileges', params=kw))
        
    @expose()
    def users(self, id_user, **kw):
        kw.update(id_user=id_user)
        redirect(url('/dashboard/privileges', params=kw))
    
    @expose('sapns/privileges/classes.html')
    def classes(self, **kw):
        
        logger = logging.getLogger('PrivilegesController.classes')
        try:
            id_user = get_paramw(kw, 'id_user', int, opcional=True)
            id_role = get_paramw(kw, 'id_role', int, opcional=True)
            if id_role:
                logger.info('role')
                who = dbs.query(SapnsRole).get(id_role)
                def has_privilege(id_class):
                    return who.has_privilege(id_class, no_cache=True)
                
            else:
                who = dbs.query(SapnsUser).get(id_user)
                #who = SapnsUser()
                def has_privilege(id_class):
                    priv = who.get_privilege(id_class)
                    if priv:
                        return priv.granted
                    
                    return None
                        
                    #cls = dbs.query(SapnsClass).get(id_class)
                    #return who.has_privilege(cls.name, no_cache=True)
    
            classes = []
            
            classes.append(Dict(id=-1,
                                id_class_p=None,
                                name='*',
                                granted=True
                                ))
            
            for cls in dbs.query(SapnsClass).order_by(SapnsClass.title):
                classes.append(Dict(id=cls.class_id,
                                    id_class_p=None,
                                    name=cls.title,
                                    granted=has_privilege(cls.class_id),
                                    ))
            
            return dict(classes=classes, show_none=id_user != None)
        
        except Exception, e:
            logger.error(e)
    
    @expose('json')
    def classp_update(self, **kw):
        
        logger = logging.getLogger('PrivilegesController.classp_update')
        try:
            id_class = get_paramw(kw, 'id_class', int)
            granted = get_paramw(kw, 'granted', strtobool, opcional=True)
            
            id_role = get_paramw(kw, 'id_role', int, opcional=True)
            if id_role:
                logger.info('role=%d' % id_role)
                who = dbs.query(SapnsRole).get(id_role)
                
            else:
                id_user = get_paramw(kw, 'id_user', int, opcional=True)
                who = dbs.query(SapnsUser).get(id_user)
                #who = SapnsUser()
                
            if granted:
                who.add_privilege(id_class)
                
            else:
                who.remove_privilege(id_class) #, delete=granted is None)
            
            return dict(status=True)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e).decode('utf-8'))
    
    @expose('sapns/privileges/attributes.html')
    def attributes(self, id_class, **kw):
        
        def _attr_privilege(cond, id_attribute):
            return dbs.query(SapnsAttrPrivilege).\
                filter(and_(cond,
                            SapnsAttrPrivilege.attribute_id == id_attribute)).\
                first()

        id_class = int(id_class)
        if id_class == -1:
            return dict(attributes=[])
        
        id_user = get_paramw(kw, 'id_user', int, opcional=True)
        id_role = get_paramw(kw, 'id_role', int, opcional=True)
        if id_role:
            #who = dbs.query(SapnsRole).get(id_role)
            attr_privilege = lambda id: \
                _attr_privilege(SapnsAttrPrivilege.role_id == id_role, id)
            
        else:
            #who = dbs.query(SapnsUser).get(id_user)
            attr_privilege = lambda id: \
                _attr_privilege(SapnsAttrPrivilege.user_id == id_user, id)
        
        # class
        cls = dbs.query(SapnsClass).get(id_class)
        
        attributes = []
        for attr in cls.attributes:
            attr_p = attr_privilege(attr.attribute_id)
            if not attr_p:
                attr_p = Dict(access='') #SapnsAttrPrivilege.ACCESS_DENIED)
            
            attributes.append(Dict(id=attr_p.attr_privilege_id,
                                   access=attr_p.access,
                                   name=attr.name,
                                   title=attr.title,
                                   id_attr=attr.attribute_id,
                                   ins_order=attr.insertion_order,
                                   ))
            
        return dict(attributes=sorted(attributes, 
                                      cmp=lambda x,y: cmp(x.ins_order, y.ins_order)),
                    show_none=id_user != None)
    
    @expose('sapns/privileges/actions.html')
    def actions(self, id_class, **kw):
        
        logger = logging.getLogger('PrivilegesController.actions')
        try:
            id_class = int(id_class)
            #id_user = get_paramw(kw, 'id_user', int, opcional=True)
            id_role = get_paramw(kw, 'id_role', int, opcional=True)
            if id_role:
                who = dbs.query(SapnsRole).get(id_role)
                
    #        else:
    #            who = dbs.query(SapnsUser).get(id_user)
            
            # class
            cls = dbs.query(SapnsClass).get(id_class)
            if cls:
                permissions = cls.permissions
                
            else:
                permissions = dbs.query(SapnsPermission).\
                    filter(SapnsPermission.class_id == None)
            
            actions = []
            for action in permissions:
                
                if action.type == SapnsPermission.TYPE_NEW:
                    pos = 1
                    
                elif action.type == SapnsPermission.TYPE_EDIT:
                    pos = 2
                    
                elif action.type == SapnsPermission.TYPE_DELETE:
                    pos = 3
                    
                elif action.type == SapnsPermission.TYPE_DOCS:
                    pos = 4
                    
                else:
                    pos = 100
                    
                actions.append(Dict(id_action=action.permission_id,
                                    display_name=_(action.display_name),
                                    name=action.permission_name,
                                    granted=who.has_permission(action.permission_id),
                                    pos=pos,
                                    ))
            
            def cmp_action(x, y):
                if x.pos == y.pos:
                    return cmp(x.name, y.name)
                
                else:
                    return cmp(x.pos, y.pos)
            
            return dict(actions=sorted(actions, cmp=cmp_action))
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)
    
    @expose('json')
    def attrp_update(self, **kw):
        
        logger = logging.getLogger('PrivilegesController.attrp_update')
        try:
            logger.info(kw)
            
            id_attribute = get_paramw(kw, 'id_attribute', int)
            access = get_paramw(kw, 'access', str)
            
            id_role = get_paramw(kw, 'id_role', int, opcional=True)
            id_user = get_paramw(kw, 'id_user', int, opcional=True)
            
            if id_role:
                who = dbs.query(SapnsRole).get(id_role)
                
            else:
                who = dbs.query(SapnsUser).get(id_user)
                
            if access:
                who.add_attr_privilege(id_attribute, access)
                
            elif isinstance(who, SapnsUser):
                who.remove_attr_privilege(id_attribute)

            return dict(status=True)
            
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e).decode('utf-8'))
        
        
    @expose('json')
    def actionp_update(self, **kw):
        
        logger = logging.getLogger('PrivilegesController.actionp_update')
        try:
            id_action = get_paramw(kw, 'id_action', int)
            granted = get_paramw(kw, 'granted', strtobool)
            
            id_role = get_paramw(kw, 'id_role', int, opcional=True)
            #id_user = get_paramw(kw, 'id_user', int, opcional=True)
            #if id_role:
            who = dbs.query(SapnsRole).get(id_role)
                
#            else:
#                who = dbs.query(SapnsUser).get(id_user)
                
            action = dbs.query(SapnsPermission).get(id_action)
                
            if granted:
                logger.info('Creating action privilege')
                who.permissions_.append(action)
                
            else:
                logger.info('Deleting action privilege')
                who.permissions_.remove(action)
                
            dbs.flush()
            
            # reset cache
            _cache = cache.get_cache(SapnsPermission.CACHE_ID)
            for user in who.users_:
                _cache.remove_value(key='%d_%d' % (user.user_id, action.class_id))

            return dict(status=True)
            
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e).decode('utf-8'))
        
    @expose('sapns/privileges/copy.html')
    def copy(self, id, **kw):
        
        id_role = int(id)
        this_role = dbs.query(SapnsRole).get(id_role)
        came_from = kw.get('came_from', '/')
        
        roles = []
        for r in dbs.query(SapnsRole).\
            filter(SapnsRole.group_id != id_role).\
            order_by(SapnsRole.display_name):
            #r = SapnsRole()
            
            roles.append(dict(id=r.group_id,
                              name=r.group_name
                              ))

        return dict(this_role=dict(id=this_role.group_id, 
                                   name=this_role.group_name),
                    roles=roles,
                    page=_('Role privileges copy'), came_from=came_from)
        
    @expose('json')
    def _copy(self, **kw):
        
        logger = logging.getLogger('PrivilegesController._copy')
        try:
            to = get_paramw(kw, 'to', int)
            role_to = dbs.query(SapnsRole).get(to)
            
            from_roles = get_paramw(kw, 'from', sj.loads)
            
            for id_from in from_roles:
                role_to.copy_privileges_from(id_from)
            
            return dict(status=True)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)