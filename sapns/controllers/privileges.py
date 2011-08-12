# -*- coding: utf-8 -*-
"""Privilege management controller"""

# turbogears imports
from tg import expose, url, config, redirect, request, require

# third party imports
from pylons import cache
from pylons.i18n import ugettext as _
#from pylons.i18n import lazy_ugettext as l_
from repoze.what import authorize #, predicates

# project specific imports
import logging
from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs

from sapns.model.sapnsmodel import SapnsUser , SapnsClass,\
    SapnsRole, SapnsAttrPrivilege, SapnsAction, SapnsActPrivilege,\
    SapnsPrivilege, SapnsUserRole, SapnsAttribute
from neptuno.dict import Dict
from neptuno.util import get_paramw, strtobool
from sqlalchemy.sql.expression import and_

__all__ = ['PrivilegesController']

class PrivilegesController(BaseController):
    
    allow_only = authorize.in_group('managers')
    
    @expose('sapns/privileges/index.html')
    def index(self, **kw):
        came_from = kw.get('came_from', '/')
        page = _('Privilege management')
        
        return dict(page=page, came_from=came_from)
    
    @expose('sapns/privileges/classes.html')
    def classes(self, **kw):
        
        id_role = get_paramw(kw, 'id_role', int, opcional=True)
        if id_role:
            who = dbs.query(SapnsRole).get(id_role)
            def has_privilege(id_class):
                return who.has_privilege(id_class, no_cache=True)
            
        else:
            id_user = get_paramw(kw, 'id_user', int, opcional=True)
            who = dbs.query(SapnsUser).get(id_user)
            def has_privilege(id_class):
                cls = dbs.query(SapnsClass).get(id_class)                
                return who.has_privilege(cls.name, no_cache=True)

        classes = []
        for cls in dbs.query(SapnsClass).order_by(SapnsClass.title):
            classes.append(Dict(id=cls.class_id,
                                id_class_p=None,
                                name=cls.title,
                                granted=has_privilege(cls.class_id),
                                ))
        
        return dict(classes=classes)
    
    @expose('json')
    def classp_update(self, **kw):
        
        logger = logging.getLogger('PrivilegesController.classp_update')
        try:
            
            id_class = get_paramw(kw, 'id_class', int)
            granted = get_paramw(kw, 'granted', strtobool)
            
            id_role = get_paramw(kw, 'id_role', int, opcional=True)
            if id_role:
                who = dbs.query(SapnsRole).get(id_role)
                
            else:
                id_user = get_paramw(kw, 'id_user', int, opcional=True)
                who = dbs.query(SapnsUser).get(id_user)
                
            if granted:
                who.add_privilege(id_class)
                
            else:
                who.remove_privilege(id_class)
            
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
        id_role = get_paramw(kw, 'id_role', int, opcional=True)
        if id_role:
            #who = dbs.query(SapnsRole).get(id_role)
            attr_privilege = lambda id: \
                _attr_privilege(SapnsAttrPrivilege.role_id == id_role, id)
            
        else:
            id_user = get_paramw(kw, 'id_user', int, opcional=True)
            #who = dbs.query(SapnsUser).get(id_user)
            attr_privilege = lambda id: \
                _attr_privilege(SapnsAttrPrivilege.user_id == id_user, id)
        
        # class
        cls = dbs.query(SapnsClass).get(id_class)
        
        attributes = []
        for attr in cls.attributes:
            attr_p = attr_privilege(attr.attribute_id)
            if not attr_p:
                attr_p = Dict(access=SapnsAttrPrivilege.ACCESS_DENIED)
            
            attributes.append(Dict(id=attr_p.attr_privilege_id,
                                   access=attr_p.access,
                                   name=attr.title,
                                   id_attr=attr.attribute_id,
                                   ins_order=attr.insertion_order,
                                   ))
            
        return dict(attributes=sorted(attributes, 
                                      cmp=lambda x,y: cmp(x.ins_order, y.ins_order)))
    
    @expose('sapns/privileges/actions.html')
    def actions(self, id_class, **kw):
        
        id_class = int(id_class)
        id_role = get_paramw(kw, 'id_role', int, opcional=True)
        if id_role:
            who = dbs.query(SapnsRole).get(id_role)
            
        else:
            id_user = get_paramw(kw, 'id_user', int, opcional=True)
            who = dbs.query(SapnsUser).get(id_user)
        
        # class
        cls = dbs.query(SapnsClass).get(id_class)
        
        actions = []
        for action in cls.actions:
            
            action_p = who.act_privilege(action.action_id)
            granted = True
            if not action_p:
                action_p = Dict()
                granted = False
                
            pos = None
            if action.type == SapnsAction.TYPE_NEW:
                pos = 1
                
            elif action.type == SapnsAction.TYPE_EDIT:
                pos = 2
                
            elif action.type == SapnsAction.TYPE_DELETE:
                pos = 3
                
            actions.append(Dict(id=action_p.actpriv_id,
                                id_action=action.action_id,
                                name=_(action.name),
                                granted=granted,
                                pos=pos,
                                ))
        
        def cmp_action(x, y):
            if x.pos == y.pos:
                return cmp(x.name, y.name)
            
            else:
                return cmp(x.pos, y.pos)
        
        return dict(actions=sorted(actions, cmp=cmp_action))
    
    @expose('json')
    def attrp_update(self, **kw):
        
        logger = logging.getLogger('PrivilegesController.attrp_update')
        try:
            id_attribute = get_paramw(kw, 'id_attribute', int)
            access = get_paramw(kw, 'access', str)
            
            id_role = get_paramw(kw, 'id_role', int, opcional=True)
            id_user = get_paramw(kw, 'id_user', int, opcional=True)
            
            if id_role:
                who = dbs.query(SapnsRole).get(id_role)
                
            else:
                who = dbs.query(SapnsUser).get(id_user)
                
            who.add_attr_privilege(id_attribute, access)
            
#            id_attr_p = get_paramw(kw, 'id_attr_p', int, opcional=True)
#            if id_attr_p:
#                attr_p = dbs.query(SapnsAttrPrivilege).get(id_attr_p)
#                
#            else:
#                attr_p = SapnsAttrPrivilege()
#                attr_p.role_id = id_role
#                attr_p.user_id = id_user 
#                attr_p.attribute_id = id_attribute
#
#            dbs.add(attr_p)
#            dbs.flush()
            
            # reset cache
            if id_user:
                ids_user = [id_user]
                
            else:
                ids_user = [ur.user_id for ur in dbs.query(SapnsUserRole).\
                            filter(SapnsUserRole.role_id == id_role)]
                
            attr = dbs.query(SapnsAttribute).get(id_attribute)
                
            for id_user in ids_user:
                _cache = cache.get_cache('class_get_attributes')
                _key = '%d_%d' % (attr.class_id, id_user)
                _cache.remove_value(key=_key)
            
            return dict(status=True)
            
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e).decode('utf-8'))
        
        
    @expose('json')
    def actionp_update(self, **kw):
        
        logger = logging.getLogger('PrivilegesController.atcp_update')
        try:
            id_action = get_paramw(kw, 'id_action', int)
            granted = get_paramw(kw, 'granted', strtobool)
            
            id_role = get_paramw(kw, 'id_role', int, opcional=True)
            id_user = get_paramw(kw, 'id_user', int, opcional=True)
            if id_role:
                who = dbs.query(SapnsRole).get(id_role)
                
            else:
                who = dbs.query(SapnsRole).get(id_user)
                
            if granted:
                logger.info('Creating action privilege')
                who.add_act_privilege(id_action)
                
            else:
                logger.info('Deleting action privilege')
                who.remove_act_privilege(id_action)
            
#            if id_action_p:
#                # delete
#                action_p = dbs.query(SapnsActPrivilege).\
#                    filter(SapnsActPrivilege.actpriv_id == id_action_p).\
#                    delete()
#                    
#                id_action_p = ''
#                
#            else:
#                # create
#                action_p = SapnsActPrivilege()
#                action_p.role_id = 
#                action_p.user_id = 
#                action_p.action_id = 
#                dbs.add(action_p)
#                
#                id_action_p = action_p.actpriv_id
#                
#            dbs.flush()
            
            return dict(status=True)
            
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e).decode('utf-8'))
        
        
        
        
        
        