# -*- coding: utf-8 -*-

"""Sapns basic data model"""

from neptuno.dict import Dict
from neptuno.util import datetostr
from pylons import cache
from pylons.i18n import ugettext as _
from sapns.model import DeclarativeBase, DBSession as dbs
from sapns.model.auth import User, user_group_table, Group, Permission, \
    group_permission_table
from sqlalchemy import MetaData, Table, ForeignKey, Column, UniqueConstraint, \
    DefaultClause
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.orm import relation
from sqlalchemy.sql.expression import and_, select, alias, desc, bindparam, func
from sqlalchemy.types import Unicode, Integer, Boolean, Date, Time, Text, \
    DateTime, BigInteger
from tg import config
import datetime as dt
import logging
import os
import re
import shutil

__all__ = ['SapnsAssignedDoc', 'SapnsAttrPrivilege', 'SapnsAttribute', 'SapnsClass',
           'SapnsDoc', 'SapnsDocFormat', 'SapnsDocType', 'SapnsMessage', 
           'SapnsMessageTo', 'SapnsPermission', 'SapnsPrivilege', 'SapnsRepo', 
           'SapnsReport', 'SapnsReportParam', 'SapnsRole', 'SapnsRolePermission', 
           'SapnsShortcut', 'SapnsUpdates', 'SapnsUser', 'SapnsUserRole',
           'SapnsView', 'SapnsViewColumn', 'SapnsViewFilter', 'SapnsViewOrder',
           'SapnsViewRelation', 
          ]

class SapnsRole(Group):
    
    users_ = relation('SapnsUser', secondary=user_group_table, backref='roles')
    permissions_ = relation('SapnsPermission', secondary=group_permission_table, backref='roles')
    
    @staticmethod
    def by_name(role_name):
        return dbs.query(SapnsRole).\
            filter(SapnsRole.group_name == role_name).\
            first()
    
    def add_privilege(self, id_class):
        return SapnsPrivilege.add_privilege(id_class, id_role=self.group_id)
        
    def remove_privilege(self, id_class, **kw):
        SapnsPrivilege.remove_privilege(id_class, id_role=self.group_id)
            
    def has_privilege(self, id_class, no_cache=False):
        def _has_privilege():
            priv = dbs.query(SapnsPrivilege).\
                filter(and_(SapnsPrivilege.role_id == self.group_id,
                            SapnsPrivilege.class_id == id_class
                            )).\
                first()
                
            if priv:
                return priv.granted
            
            else:
                return False
                
        _cache = cache.get_cache('role_has_privilege')
        _key = '%s_%d' % (id_class, self.group_id)
        if no_cache:
            _cache.remove_value(key=_key)
                
        return _cache.get_value(key=_key, createfunc=_has_privilege, expiretime=3600)
            
    def attr_privilege(self, id_attribute):
        return SapnsAttrPrivilege.get_privilege(id_attribute, id_role=self.group_id)
            
    def add_attr_privilege(self, id_attribute, access):
        return SapnsAttrPrivilege.add_privilege(id_attribute, access, id_role=self.group_id)
    
    def has_permission(self, id_permission):
        return SapnsRolePermission.has_permission(self.group_id, id_permission)
    
    def copy_privileges_from(self, id_from_role):
        
        #logger = logging.getLogger('SapnsRole.copy_privileges_from')

        # class privileges
        for old_p in dbs.query(SapnsPrivilege).\
                filter(SapnsPrivilege.role_id == id_from_role):
            
            new_p = dbs.query(SapnsPrivilege).\
                filter(and_(SapnsPrivilege.role_id == self.group_id,
                            SapnsPrivilege.class_id == old_p.class_id,
                            )).\
                first()
            
            if not new_p:
                new_p = SapnsPrivilege()
                new_p.role_id = self.group_id
                new_p.class_id = old_p.class_id
                
            new_p.granted = old_p.granted
                
            dbs.add(new_p)
            dbs.flush()
        
        # attribute privileges
        for old_attrp in dbs.query(SapnsAttrPrivilege).\
                filter(SapnsAttrPrivilege.role_id == id_from_role):
            
            new_attrp = dbs.query(SapnsAttrPrivilege).\
                    filter(and_(SapnsAttrPrivilege.role_id == self.group_id,
                                SapnsAttrPrivilege.attribute_id == old_attrp.attribute_id
                                )).\
                    first()
                    
            if not new_attrp:
                new_attrp = SapnsAttrPrivilege()
                new_attrp.role_id = self.group_id
                new_attrp.attribute_id = old_attrp.attribute_id
            
            new_attrp.access = old_attrp.access
                
            dbs.add(new_attrp)
            dbs.flush()
        
        # permissions
        for perm in dbs.query(SapnsPermission):
            
            p0 = dbs.query(SapnsRolePermission).\
                    filter(and_(SapnsRolePermission.role_id == id_from_role,
                                SapnsRolePermission.permission_id == perm.permission_id,
                                )).\
                    first()
                    
            if p0:
                p = dbs.query(SapnsRolePermission).\
                        filter(and_(SapnsRolePermission.role_id == self.group_id,
                                    SapnsRolePermission.permission_id == perm.permission_id,
                                    )).\
                        first()
                        
                if not p:
                    new_rp = SapnsRolePermission()
                    new_rp.role_id = self.group_id
                    new_rp.permission_id = perm.permission_id
                    dbs.add(new_rp)
                    dbs.flush()
                    
            else:
                # borrar el permiso
                p = dbs.query(SapnsRolePermission).\
                        filter(and_(SapnsRolePermission.role_id == self.group_id,
                                    SapnsRolePermission.permission_id == perm.permission_id,
                                    )).\
                        delete()
                        
                dbs.flush()
                   
#    def add_act_privilege(self, id_action):
#        return SapnsActPrivilege.add_privilege(id_action, id_role=self.group_id)
#
#    def act_privilege(self, id_action):
#        return SapnsActPrivilege.get_privilege(id_action, id_role=self.group_id)
#
#    def has_act_privilege(self, id_action):
#        return self.act_privilege(id_action) != None
#
#    def remove_act_privilege(self, id_action):
#        SapnsActPrivilege.remove_privilege(id_action, id_role=self.group_id)

class SapnsUserRole(DeclarativeBase):
    
    __tablename__ = 'sp_user_role'
    __table_args__ = (None, dict(useexisting=True))
    
    user_id = Column('id_user', Integer,
                     ForeignKey('sp_users.id',
                                onupdate="CASCADE", ondelete="CASCADE"), 
                     primary_key=True)
                          
    role_id = Column('id_role', Integer, 
                     ForeignKey('sp_roles.id',
                                onupdate="CASCADE", ondelete="CASCADE"), 
                     primary_key=True)

# inherited class from "User"
class SapnsUser(User):
    
    authored_docs = relation('SapnsDoc', backref='author')
    
    def entry_point(self):
        return self.groups[0].entry_point
    
    def get_dashboard(self):
        return dbs.query(SapnsShortcut).\
            filter(and_(SapnsShortcut.user_id == self.user_id,
                        SapnsShortcut.parent_id == None)).\
            first()
    
    def get_dataexploration(self):
        return dbs.query(SapnsShortcut).\
            filter(and_(SapnsShortcut.user_id == self.user_id,
                        func.upper(SapnsShortcut.title) == func.upper(u'Data exploration'),
                        )).\
            first()
    
    def get_shortcuts(self, id_parent=None):
        
        logger = logging.getLogger('SapnsUser.get_shortcuts')
        
        if not id_parent:
            id_parent = self.get_dashboard().shortcut_id
            
        id_parent = int(id_parent)
            
        def __get_shortcuts(id_parent):
            logger.info('Getting shortcuts of [%d]' % id_parent)
            
            shortcuts = []
            for sc, ac, cl in dbs.query(SapnsShortcut, SapnsPermission, SapnsClass).\
                    outerjoin((SapnsPermission,
                               SapnsPermission.permission_id == SapnsShortcut.permission_id)).\
                    outerjoin((SapnsClass, 
                               SapnsClass.class_id == SapnsPermission.class_id)).\
                    filter(and_(SapnsShortcut.user_id == self.user_id,
                                SapnsShortcut.parent_id == id_parent)).\
                    order_by(SapnsShortcut.order):
                
                url = ''
                type_ = ''
                class_ = ''
                if ac:
                    url = ac.url
                    type_ = ac.type
                    
                    if cl:
                        class_ = cl.name 
                                
                shortcuts.append(dict(url=url, 
                                      order=sc.order,
                                      title=_(sc.title),
                                      action_type=type_,
                                      cls=class_,
                                      parent=sc.parent_id, 
                                      id=sc.shortcut_id))
            
            return shortcuts

        def _get_shortcuts():
            return __get_shortcuts(id_parent)
        
        _cache = cache.get_cache('user_get_shortcuts')
        _key = '%d_%d' % (self.user_id, id_parent)
        return _cache.get_value(key=_key, createfunc=_get_shortcuts, expiretime=3600)
    
    def copy_from(self, other_id):
        
        logger = logging.getLogger('SapnsUser.copy_from')
        try:
            # shortcuts
            logger.info('Copying shortcuts')
            parents = {}
            for sc in dbs.query(SapnsShortcut).\
                    filter(SapnsShortcut.user_id == other_id):
                
                sc_copy = SapnsShortcut()
                sc_copy.title = sc.title
                sc_copy.parent_id = sc.parent_id
                sc_copy.user_id = self.user_id
                sc_copy.permission_id = sc.permission_id
                sc_copy.order = sc.order
                
                dbs.add(sc_copy)
                dbs.flush()
                
                parents[sc.shortcut_id] = sc_copy.shortcut_id
                
            logger.info('Updating parents')
            for sc_copy in dbs.query(SapnsShortcut).\
                    filter(and_(SapnsShortcut.user_id == self.user_id,
                                SapnsShortcut.parent_id != None)):

                # update parent shortcut
                sc_copy.parent_id = parents[sc_copy.parent_id]
                dbs.add(sc_copy)
                dbs.flush()
                
            # privileges (on classes)
            logger.info('Copying privileges')
            for priv in dbs.query(SapnsPrivilege).\
                    filter(SapnsPrivilege.user_id == other_id):

                priv_copy = SapnsPrivilege()
                priv_copy.class_id = priv.class_id
                priv_copy.user_id = self.user_id
                
                dbs.add(priv_copy)
                dbs.flush()
            
            # attribute privileges
            logger.info('Copying attribute privileges')
            for ap in dbs.query(SapnsAttrPrivilege).\
                    filter(SapnsAttrPrivilege.user_id == other_id):
                
                ap_copy = SapnsAttrPrivilege()
                ap_copy.user_id = self.user_id
                ap_copy.attribute_id = ap.attribute_id
                ap_copy.access = ap.access
                
                dbs.add(ap_copy)
                dbs.flush()
                
            logger.info('Copying roles')
            cond = user_group_table.c.id_user == other_id #@UndefinedVariable
            for rl in dbs.execute(user_group_table.select(cond)):
                copy_rl = dict(id_user=self.user_id, id_role=rl.id_role)
                ins_rl = user_group_table.insert(values=copy_rl)
                dbs.execute(ins_rl)
                dbs.flush()
                
        except Exception, e:
            logger.error(e)
            
    def from_list(self, title, url):
        
        # new action
        action_link = SapnsPermission()
        action_link.class_id = None
        action_link.type = SapnsPermission.TYPE_OBJECT
        action_link.permission_name = title
        action_link.display_name = title
        action_link.url = url
        
        dbs.add(action_link)
        dbs.flush()
        
        # new shortcut
        sc_link = SapnsShortcut()
        sc_link.permission_id = action_link.permission_id
        sc_link.title = title
        sc_link.user_id = self.user_id
        
        dbs.add(sc_link)
        dbs.flush()

        # add this search as a dashboard's shortcut        
        dboard = self.get_dashboard()
        dboard.add_child(sc_link.shortcut_id, copy=False)
        
        # reset cache for this user's dashboard
        _key = '%d_%d' % (self.user_id, dboard.shortcut_id)
        cache.get_cache('user_get_shortcuts').remove_value(key=_key)
    
    def has_privilege(self, cls, no_cache=False):
        
        def _has_privilege():
            return SapnsPrivilege.has_privilege(self.user_id, cls)            
        
        _cache = cache.get_cache('user_has_privilege')
        _key = '%s_%d' % (cls, self.user_id)
        if no_cache:
            _cache.remove_value(key=_key)
            
        return _cache.get_value(key=_key, createfunc=_has_privilege, expiretime=3600)
    
    def add_privilege(self, id_class):
        return SapnsPrivilege.add_privilege(id_class, id_user=self.user_id)
    
    def remove_privilege(self, id_class, delete=False):
        SapnsPrivilege.remove_privilege(id_class, id_user=self.user_id, delete=delete)
        
    def get_privilege(self, id_class):
        return SapnsPrivilege.get_privilege(id_class, id_user=self.user_id)
    
    def attr_privilege(self, id_attribute):
        return SapnsAttrPrivilege.get_privilege(id_attribute, id_user=self.user_id)
    
    def remove_attr_privilege(self, id_attribute):
        SapnsAttrPrivilege.remove_privilege(id_attribute, id_user=self.user_id, remove=True)
            
    def add_attr_privilege(self, id_attribute, access):
        return SapnsAttrPrivilege.add_privilege(id_attribute, access, id_user=self.user_id)
    
    def has_permission(self, name):
        return dbs.query(SapnsPermission).\
            join((SapnsRolePermission,
                  SapnsRolePermission.permission_id == SapnsPermission.permission_id)).\
            join((SapnsRole,
                  SapnsRole.group_id == SapnsRolePermission.role_id)).\
            join((SapnsUserRole,
                  SapnsUserRole.role_id == SapnsRole.group_id)).\
            filter(and_(SapnsUserRole.user_id == self.user_id,
                        SapnsPermission.permission_name == name)).\
            first() != None
            
#    def act_privilege(self, id_action):
#        return SapnsActPrivilege.get_privilege(id_action, id_user=self.user_id)
#            
#    def add_act_privilege(self, id_action):
#        SapnsActPrivilege.add_privilege(id_action, id_user=self.user_id)
#            
#    def has_act_privilege(self, id_action):
#        return SapnsActPrivilege.has_privilege(self.user_id, id_action)
#    
#    def remove_act_privilege(self, id_action):
#        SapnsActPrivilege.remove_privilege(id_action, id_user=self.user_id)
    
    def get_view_name(self, cls):
        
        #logger = logging.getLogger('get_view_name')
        
        def _get_view_name():
            
            #logger.info('getting view name...')
            
            meta = MetaData(bind=dbs.bind)
            prefix = config.get('views_prefix', '_view_')
            try:
                # user's view
                # "_view_alumnos_1"
                view_name = '%s%s_%d' % (prefix, cls, self.user_id)
                Table(view_name, meta, autoload=True)
                view = view_name
            
            except NoSuchTableError:
                # general view
                # "_view_alumnos"
                try:
                    view_name = '%s%s' % (prefix, cls)
                    Table(view_name, meta, autoload=True)
                    view = view_name
            
                except NoSuchTableError:
                    # "raw" table
                    # "alumnos"
                    view = cls
                    
            return view
                    
        _cache = cache.get_cache('user_get_view_name')
        return _cache.get_value(key='%s_%d' % (cls, self.user_id),
                                createfunc=_get_view_name, expiretime=3600)
    
    def get_messages(self):
        
        def _get_messages():
            messages = []
            for msg, msgto, userfrom in \
                    dbs.query(SapnsMessage, SapnsMessageTo, SapnsUser).\
                    join((SapnsMessageTo, 
                          SapnsMessageTo.message_id == SapnsMessage.message_id)).\
                    join((SapnsUser, SapnsUser.user_id == SapnsMessage.user_from_id)).\
                    filter(SapnsMessageTo.user_to_id == self.user_id):
                
                messages.append(dict(id=msg.message_id,
                                     from_id=userfrom.user_id,
                                     from_name=userfrom.display_name,
                                     read=msgto.read, subject=msg.subject,
                                     body=msg.body, body_title=msg.body[:30]))
            
            return messages
        
        _cache = cache.get_cache('user_get_messages')
        return _cache.get_value(key=self.user_id, createfunc=_get_messages,
                                expiretime=120)
    
    def messages(self):
        n = dbs.query(SapnsMessageTo).\
                filter(SapnsMessageTo.user_to_id == self.user_id).\
                count()
                
        return n
    
    def unread_messages(self):
        """Returns the number of unread messages of this users"""
        
        n = dbs.query(SapnsMessageTo).\
                filter(and_(SapnsMessageTo.user_to_id == self.user_id,
                            SapnsMessageTo.is_read == False)).\
                count()
                
        return n
    
    def register_doc(self, pathtofile, title, id_repo, id_doctype):
        
        # create a new doc
        new_doc = SapnsDoc()
        new_doc.repo_id = id_repo
        new_doc.doctype_id = id_doctype
        new_doc.title = title
        new_doc.filename = os.path.basename(pathtofile)
        new_doc.author_id = self.user_id
        
        dbs.add(new_doc)
        dbs.flush()
        
        dst_path = os.path.join(new_doc.repo.path, '%d' % new_doc.doc_id)
        shutil.copy(pathtofile, dst_path)
        
#SapnsRole.users_ = relation(SapnsUser, secondary=user_group_table, backref='roles')

class SapnsShortcut(DeclarativeBase):
    """Shortcuts sapns base table"""

    __tablename__ = 'sp_shortcuts'

    shortcut_id = Column('id', Integer, autoincrement=True, primary_key=True)
    title = Column(Unicode(50))
    order = Column(Integer)
    parent_id = Column('id_parent_shortcut', Integer, 
                       ForeignKey('sp_shortcuts.id',
                                  onupdate='CASCADE', ondelete='CASCADE'))
    
    user_id = Column('id_user', Integer, 
                     ForeignKey('sp_users.id', 
                                onupdate='CASCADE', ondelete='CASCADE'), 
                     nullable=False)
    
    permission_id = Column('id_permission', Integer,
                           ForeignKey('sp_permission.id',
                                      onupdate='CASCADE', ondelete='SET NULL')) #, nullable=False)
    # permission
    
    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u'<Shortcut: "%s" user=%s, action=%s>' % \
            (self.title, self.user, self.permission or '')
    
    def by_order(self, order, comp=0):
        """Return a 'child' shortcut (of this) with the indicated 'order'"""
        
        logger = logging.getLogger('SapnsShortcut.by_order')
        logger.info('order=%d' % order)
        
        if comp == -1:
            cond = SapnsShortcut.order <= order
            order = desc(SapnsShortcut.order)
            
        elif comp == 1:
            cond = SapnsShortcut.order >= order
            order = SapnsShortcut.order
            
        else:
            cond = SapnsShortcut.order == order
            order = None #SapnsShortcut.order
        
        sc = dbs.query(SapnsShortcut).\
                filter(and_(SapnsShortcut.parent_id == self.shortcut_id,
                            cond)).\
                order_by(order).\
                first()
                
        return sc
    
    def next_order(self):
        """Returns the next order for a child shortcut."""
        
        sc = dbs.query(SapnsShortcut).\
                filter(and_(SapnsShortcut.parent_id == self.shortcut_id,
                            SapnsShortcut.order != None)).\
                order_by(desc(SapnsShortcut.order)).\
                first()
                
        if not sc:
            return 0
        
        else:
            return (sc.order or 0) + 1
        
    def add_child(self, id_shortcut, copy=True):
        
        if copy:
            # the shortcut to be copied
            sc = dbs.query(SapnsShortcut).get(id_shortcut)
            
            if not sc:
                raise Exception('That shortcut does not exist [%s]' % id_shortcut)

            # the "copy"            
            new_sc = SapnsShortcut()
            new_sc.user_id = self.user_id
            new_sc.title = sc.title
            new_sc.permission_id = sc.permission_id
            
        else:
            new_sc = dbs.query(SapnsShortcut).get(id_shortcut)
        
        new_sc.parent_id = self.shortcut_id
        new_sc.order = self.next_order()
        
        dbs.add(new_sc)
        dbs.flush()
        
    REORDER_TYPE_UP = 'up'
    REORDER_TYPE_DOWN = 'down'
        
    def reorder(self, type_='up'):
        
        logger = logging.getLogger('SapnsShortcut.reorder')
        logger.info(unicode(self))
        
        def _reorder(this, that):
            aux = that.order
            that.order = this.order
            this.order = aux
            
            dbs.add(this)
            dbs.add(that)
            dbs.flush()
            
        if type_ == SapnsShortcut.REORDER_TYPE_UP:
            if self.order > 0:
                next_sc = self.parent.by_order(self.order-1, -1)
            
            else:
                raise Exception('It is not possible to go upper')
            
        elif type_ == SapnsShortcut.REORDER_TYPE_DOWN:
            if self.order < self.parent.next_order()-1:
                next_sc = self.parent.by_order(self.order+1, +1)
            
            else:
                raise Exception('It is not possible to go deeper')
            
        logger.info(next_sc.title)
            
        _reorder(self, next_sc)

# TODO: 1-to-1 autoreference relation
SapnsShortcut.parent = \
    relation(SapnsShortcut,
             backref='children',
             uselist=False,
             remote_side=[SapnsShortcut.shortcut_id],
             primaryjoin=SapnsShortcut.shortcut_id == SapnsShortcut.parent_id)
    
SapnsUser.shortcuts = \
    relation(SapnsShortcut,
             backref='user',
             primaryjoin=SapnsUser.user_id == SapnsShortcut.user_id)
   
class SapnsClass(DeclarativeBase):
    """List of sapns tables"""

    __tablename__ = 'sp_classes'
    __table_args__ = (UniqueConstraint('name'), {})
    
    class_id = Column('id', Integer, autoincrement=True, primary_key=True)
    
    name = Column(Unicode(50), nullable=False)
    title = Column(Unicode(100), nullable=False)
    description = Column(Text)
    parent_class_id = Column('id_parent_class', Integer, 
                             ForeignKey('sp_classes.id', 
                                        onupdate='CASCADE', ondelete='CASCADE'))
    
    is_logged = Column(Boolean, default=False)
    
    #attributes
    privileges = relation('SapnsPrivilege', backref='class_')
    permissions = relation('SapnsPermission', backref='class_')
    
    CACHE_ID_ATTR = 'class_get_attributes'
    
    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.title)
    
    def __repr__(self):
        return unicode(self).encode('utf-8')
    
    @staticmethod
    def by_name(class_name, parent=True):
        """
        Returns the SapnsClass whose name is "class_name"
        IN
          class_name  <unicode>
          
        OUT
          <SapnsClass>
        """
        
        logger = logging.getLogger('SapnsClass.by_name')
        logger.info('Looking up a class by name...%s' % class_name)
        
        cls = dbs.query(SapnsClass).\
            filter(SapnsClass.name == class_name).\
            first()
            
        logger.info(cls)
            
        if parent and cls.parent_class_id:
            logger.info('Getting parent class...')
            cls = dbs.query(SapnsClass).get(cls.parent_class_id)
            
        return cls
                
    @staticmethod
    def class_titles(class_name):
        
        logger = logging.getLogger(__name__ + '/class_titles')
        
        date_fmt = config.get('formats.date', default='%m/%d/%Y')
        
        def __class_title(class_name, qry=None, attr=None):
            
            try:
                meta = MetaData(bind=dbs.bind)
                cls = SapnsClass.by_name(class_name)
                tbl = alias(Table(cls.name, meta, autoload=True))
                
                names = []
                types = []
                
                if qry is None:
                    qry = tbl
                    names.append(tbl.c.id.label('id'))
                    types.append(SapnsAttribute.TYPE_INTEGER)
                    
                else:
                    qry = qry.outerjoin(tbl, attr == tbl.c.id)
                    
                for r in cls.reference():
                    
                    logger.info(r['name'])
                    
                    if not r['related_class_id']:
                        names.append(tbl.c[r['name']])
                        types.append(r['type'])
                        
                    else:
                        rel_class = dbs.query(SapnsClass).get(r['related_class_id'])
                        names_rel, types_rel, qry = \
                            __class_title(rel_class.name, qry=qry, attr=tbl.c[r['name']])

                        names += names_rel
                        types += types_rel
                        
                return names, types, qry
            
            except Exception, e:
                logger.error(e)
                
        names, types, qry = __class_title(class_name, qry=None)
        
        MAX_VALUES = 5000
        
        sel = select(names, from_obj=qry, use_labels=True).\
                order_by(*tuple(names[1:])).\
                limit(MAX_VALUES)
                
        logger.info(sel)
        
        titles = []
        for row in dbs.execute(sel):
            
            cols = []
            for n, t in zip(names[1:], types[1:]):
                
                value = row[n]
                
                if value:
                    if t == SapnsAttribute.TYPE_DATE:
                        cols.append(datetostr(value, fmt=date_fmt))
                        
                    # rest of types
                    else:
                        cols.append(unicode(value))
                        
                else:
                    cols.append('')
                
            title = '%s  [%d]' % ('.'.join(cols), row.id)
                
            titles.append(dict(id=row.id, title=title))
                    
        return titles
    
    class ObjectTitle(object):
         
        def __init__(self, class_name):
            self.class_name = class_name
            self.date_fmt = config.get('formats.date', default='%m/%d/%Y')
            
            meta = MetaData(bind=dbs.bind)
            self.cls = SapnsClass.by_name(class_name)
            tbl = Table(self.cls.name, meta, autoload=True)
            self.sel = \
                select([tbl],
                       from_obj=tbl,
                       whereclause=tbl.c.id == bindparam('id_object'))
                
            self.related_class = {}
         
        def title(self, id_object):
             
            if not id_object:
                return ''
             
            row = dbs.execute(self.sel, params=dict(id_object=id_object)).fetchone()
            ref = []
            for r in self.cls.reference():
                
                if not r['related_class_id']:
                    
                    value = row[r['name']]
                    if value:
                        if r['type'] == SapnsAttribute.TYPE_DATE:
                            value = datetostr(value, fmt=self.date_fmt)
                            
                        else:
                            value = unicode(value)
                    else:
                        value = '' 
                    
                    ref.append(value)
                    
                else:
                    if not self.related_class.has_key(r['related_class_id']):
                        # related attribute
                        rel_class = dbs.query(SapnsClass).get(r['related_class_id'])
                        ot = SapnsClass.ObjectTitle(rel_class.name)
                        self.related_class[r['related_class_id']] = ot
                    else:
                        ot = self.related_class[r['related_class_id']]
                        
                    ref.append(ot.title(row[r['name']]))
                    
            return '.'.join(ref)
    
    @staticmethod
    def object_title(class_name, id_object):
        
        logger = logging.getLogger('object_title')
        
        _title = SapnsClass.ObjectTitle(class_name).title(id_object)
        
        if id_object and not _title:
            cls = SapnsClass.by_name(class_name)
            _title = '[%s: %s]' % (cls.title, id_object)
            logger.info(u'no_title: %s' % _title)
            
        return _title
    
    def sorted_actions(self, id_user):
        """
        Returns a list of actions associated with this class.
        
        OUT
          [{"title":      <unicode>, 
            "url":        <unicode>, 
            "require_id": <bool>, 
            "type":       <unicode>}, ...]
        """
        
        def _sorted_actions():
            
            #user = dbs.query(SapnsUser).get(id_user)
            #user = 
            
            actions = []
            for ac in dbs.query(SapnsPermission).\
                    filter(and_(SapnsPermission.class_id == self.class_id,
                                SapnsPermission.type != None,
                                SapnsPermission.type != SapnsPermission.TYPE_LIST,
                                )):
                
                # does this user has privilege on this action?
                user = dbs.query(SapnsUser).get(id_user)
                p_id = [p.permission_id for p in user.permissions]
                if ac.permission_id in p_id: 
                # SapnsActPrivilege.has_privilege(id_user, ac.action_id):
                    
                    url = ac.url
                    if url and url[-1] != '/':
                        url += '/'
                        
                    require_id = ac.requires_id # True
                    pos = 100
                        
                    if ac.type == SapnsPermission.TYPE_NEW:
                        if not ac.url:
                            url = SapnsPermission.URL_NEW
                            
                        require_id = False
                        pos = 1
                    
                    elif ac.type == SapnsPermission.TYPE_EDIT:
                        if not ac.url:
                            url = SapnsPermission.URL_EDIT
                            
                        require_id = True
                        pos = 2
                    
                    elif ac.type == SapnsPermission.TYPE_DELETE:
                        if not ac.url:
                            url = SapnsPermission.URL_DELETE
                            
                        require_id = True
                        pos = 3
                        
                    elif ac.type == SapnsPermission.TYPE_DOCS:
                        if not ac.url:
                            url = SapnsPermission.URL_DOCS
                            
                        require_id = True
                        pos = 4
                        
                    p_name = re.search(r'^\w+#(\w+)', ac.permission_name, re.I)
                    if p_name:
                        p_name = p_name.group(1)
                        
                    actions.append(Dict(name=p_name or '', title=_(ac.display_name), 
                                        type=ac.type, url=url, require_id=require_id, 
                                        pos=pos))
                
            def cmp_act(x, y):
                if x.pos == y.pos:
                    return cmp(x.title, y.title)
                
                else:
                    return cmp(x.pos, y.pos)
        
            return sorted(actions, cmp=cmp_act)
        
        _cache = cache.get_cache(SapnsPermission.CACHE_ID)
        return _cache.get_value(key='%d_%d' % (id_user, self.class_id), 
                                createfunc=_sorted_actions, expiretime=3600)
    
    def insertion(self):
        """
        Return the list of attributes in "order of insertion" for this class.
        
        OUT
          [{"id": <int>, "title": <unicode>, "name": <unicode>,
            "required": <bool>, "visible": <bool>}, ...]
        """
        
        ins = []
        for attr in dbs.query(SapnsAttribute).\
                filter(SapnsAttribute.class_id == self.class_id).\
                order_by(SapnsAttribute.insertion_order).\
                all():
            
            ins.append(dict(id=attr.attribute_id, title=attr.title,
                            name=attr.name, required=attr.required, 
                            visible=attr.visible))
            
        return ins
    
    def reference(self, all=False):
        """
        Returns the list of attributes in "order of reference" for this class.
        
        IN
          all  <bool> (optional)
          
        OUT
          [{"id": <int>, "title": <unicode>, "name": <unicode>, 
            "included": <bool>, "visible": <bool>, 
            "related_class_id": <int>}, ...]
        """
        
        cond_all = None
        if not all:
            cond_all = SapnsAttribute.reference_order != None
        
        ref = []
        for attr in dbs.query(SapnsAttribute).\
                filter(and_(SapnsAttribute.class_id == self.class_id,
                            cond_all)).\
                order_by(SapnsAttribute.reference_order).\
                all():
            
            ref.append(dict(id=attr.attribute_id, title=attr.title, 
                            name=attr.name, included=attr.reference_order != None,
                            type=attr.type, visible=attr.visible, 
                            related_class_id=attr.related_class_id,
                            ))
            
        return ref
    
    def attr_by_name(self, attr_name):
        """
        Returns a SapnsAttribute of this class whose name is "attr_name".
        
        IN
          attr_name  <str>
          
        OUT
          <SapnsAttribute>
        """
        
        attr = dbs.query(SapnsAttribute).\
                filter(and_(SapnsAttribute.class_id == self.class_id,
                            SapnsAttribute.name == attr_name,
                            )).\
                first()
                
        return attr
    
    def related_classes(self):
        """
        Returns a list of classes related with this and the attribute 
        the relationship is built on.
        
        OUT
          [{"id":         <int>, 
            "name":       <unicode>, 
            "title":      <unicode>,
            "attr_id":    <int>, 
            "attr_name":  <unicode>,
            "attr_title": <unicode>}, ...]
        """
        
        def _related_classes():
            
            rel_classes = []
            for cls, attr in dbs.query(SapnsClass, SapnsAttribute).\
                    join((SapnsAttribute, 
                          SapnsAttribute.class_id == SapnsClass.class_id)).\
                    filter(SapnsAttribute.related_class_id == self.class_id).\
                    order_by(SapnsClass.title, SapnsAttribute.insertion_order):
                
                rc = dict(id=cls.class_id, name=cls.name, title=cls.title,
                          attr_id=attr.attribute_id,
                          attr_name=attr.name, attr_title=attr.title)
                
                rel_classes.append(rc)
                
            return rel_classes
        
        _cache = cache.get_cache('related_classes')
        return _cache.get_value(key=self.class_id, createfunc=_related_classes,
                                expiretime=3600)
        
    # get attributes
    def get_attributes(self, id_user):
        
        #logger = logging.getLogger('SapnsClass.get_attributes')

        def _get_attributes():
            
            _cmp = SapnsAttrPrivilege.cmp_access
            
            class_attr_priv = {}
            i = 0
            last_attr = None
            
            # role based
            # attr privileges
            for attr_priv in dbs.query(SapnsAttrPrivilege).\
                    join((SapnsRole,
                          SapnsRole.group_id == SapnsAttrPrivilege.role_id)).\
                    join((SapnsUserRole,
                          and_(SapnsUserRole.role_id == SapnsRole.group_id,
                               SapnsUserRole.user_id == id_user
                               ))).\
                    join((SapnsAttribute,
                          and_(SapnsAttribute.attribute_id == SapnsAttrPrivilege.attribute_id,
                               SapnsAttribute.class_id == self.class_id,
                               ))).\
                    filter(SapnsAttrPrivilege.access != SapnsAttrPrivilege.ACCESS_DENIED).\
                    order_by(SapnsAttribute.insertion_order):

                if last_attr != attr_priv.attribute_id:
                    i += 1
                    
                last_attr = attr_priv.attribute_id

                if class_attr_priv.has_key(attr_priv.attribute_id):
                    if _cmp(class_attr_priv[attr_priv.attribute_id].access, attr_priv.access) == -1:
                        class_attr_priv[attr_priv.attribute_id] = Dict(access=attr_priv.access, pos=i)
    
                else:
                    class_attr_priv[attr_priv.attribute_id] = Dict(access=attr_priv.access, pos=i)

            user = dbs.query(SapnsUser).get(id_user)

            # class attributes (insertion order, field_regex, ...)
            class_attributes = []
            for attr in dbs.query(SapnsAttribute).\
                    filter(SapnsAttribute.class_id == self.class_id).\
                    order_by(SapnsAttribute.insertion_order):

                # what about the privileges on the related class?
                if class_attr_priv.has_key(attr.attribute_id): 
                
                    if attr.related_class_id and \
                    class_attr_priv[attr.attribute_id].access == SapnsAttrPrivilege.ACCESS_READWRITE:
                    
                        # related class
                        rc = dbs.query(SapnsClass).get(attr.related_class_id)
                        
                        if not user.has_privilege(rc.name) or \
                        not user.has_permission(u'%s#%s' % (rc.name, SapnsPermission.TYPE_LIST)):
                            class_attr_priv[attr.attribute_id].access = SapnsAttrPrivilege.ACCESS_READONLY
                
                    class_attributes.append(
                        Dict(id=attr.attribute_id,
                             name=attr.name,
                             title=attr.title,
                             type=attr.type,
                             required=attr.required,
                             related_class_id=attr.related_class_id,
                             field_regex=attr.field_regex,
                            ))
            
            # merge list of attributes and privileges on those attributes in one list
            return zip(class_attributes, sorted(class_attr_priv.values(), 
                                                cmp=lambda x, y: cmp(x.pos, y.pos)))
            
        _cache = cache.get_cache(SapnsClass.CACHE_ID_ATTR)
        return _cache.get_value(key='%d_%d' % (self.class_id, id_user),
                                createfunc=_get_attributes, expiretime=3600)

class SapnsAttribute(DeclarativeBase):
    
    __tablename__ = 'sp_attributes'
    __table_args__ = (UniqueConstraint('name', 'id_class'), {})

    attribute_id = Column('id', Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(60), nullable=False)
    title = Column(Unicode(100), nullable=False)
    
    TYPE_INTEGER = 'int'
    TYPE_BOOLEAN = 'bool'
    TYPE_FLOAT = 'float'
    TYPE_STRING = 'str'
    TYPE_MEMO = 'memo'
    TYPE_DATE = 'date'
    TYPE_TIME = 'time'
    TYPE_DATETIME = 'datetime'
    TYPE_IMAGE = 'img'
    TYPE_URL = 'url'
    
    type = Column(Unicode(20), nullable=False)
    required = Column(Boolean, DefaultClause('false'), default=False)
    reference_order = Column(Integer)
    insertion_order = Column(Integer)
    visible = Column(Boolean, DefaultClause('true'), default=True)
    field_regex = Column(Text)
    
    class_id = Column('id_class', Integer, 
                      ForeignKey('sp_classes.id', 
                                 onupdate='CASCADE', ondelete='CASCADE'), 
                      nullable=False)
    # class_
    
    related_class_id = Column('id_related_class', Integer, 
                              ForeignKey('sp_classes.id',
                                         onupdate='CASCADE', ondelete='SET NULL'))
    # related_class
    
    attr_priv = relation('SapnsAttrPrivilege', backref='attribute')
    
    def __unicode__(self):
        return u'<%s> %s %s (%s)' % (unicode(self.class_), self.title, self.name, self.type)
    
    def __repr__(self):
        return unicode(self).encode('utf-8')
    
SapnsClass.attributes = \
    relation(SapnsAttribute, backref='class_',
             primaryjoin=SapnsClass.class_id == SapnsAttribute.class_id)
    
SapnsClass.related_attributes = \
    relation(SapnsAttribute, backref='related_class',
             primaryjoin=SapnsClass.class_id == SapnsAttribute.related_class_id)

class SapnsPrivilege(DeclarativeBase):
    
    __tablename__ = 'sp_privileges'
    __table_args__ = (UniqueConstraint('id_user', 'id_class'),
                      UniqueConstraint('id_role', 'id_class'), {})
    
    privilege_id = Column('id', Integer, primary_key=True, autoincrement=True)
    
    user_id = Column('id_user', Integer, 
                     ForeignKey('sp_users.id',
                                onupdate='CASCADE', ondelete='CASCADE'))

    role_id = Column('id_role', Integer,
                     ForeignKey('sp_roles.id',
                                onupdate='CASCADE', ondelete='CASCADE'))

    class_id = Column('id_class', Integer, 
                      ForeignKey('sp_classes.id', 
                                 onupdate='CASCADE', ondelete='CASCADE'), 
                      nullable=False)
    # class_
    
    granted = Column(Boolean, nullable=False, default=True)
    
    CACHE_ID = 'user_class_privilege'

    @staticmethod
    def has_privilege(id_user, cls):
        
        #logger = logging.getLogger('SapnsPrivilege.has_privilege')

        if isinstance(cls, (str, unicode)):
            id_class = SapnsClass.by_name(cls).class_id
            
        else:
            id_class = cls
        
        def _has_privilege():
            
            #logger.info('> class=%s' % cls)
            
            # role based
            priv = dbs.query(SapnsPrivilege).\
                join((SapnsRole,
                      SapnsRole.group_id == SapnsPrivilege.role_id)).\
                join((SapnsUserRole,
                      and_(SapnsUserRole.role_id == SapnsRole.group_id,
                           SapnsUserRole.user_id == id_user))).\
                filter(and_(SapnsPrivilege.class_id == id_class,
                            SapnsPrivilege.granted,
                            )).\
                first()
               
            return priv != None
        
        _cache = cache.get_cache(SapnsPrivilege.CACHE_ID)
        return _cache.get_value(key='%d_%d' % (id_user, id_class),
                                createfunc=_has_privilege, expiretime=1)
    
    @staticmethod
    def get_privilege(id_class, **kw):
        return dbs.query(SapnsPrivilege).\
            filter(and_(SapnsPrivilege.class_id == id_class,
                        SapnsPrivilege.role_id == kw.get('id_role'),
                        SapnsPrivilege.user_id == kw.get('id_user')
                        )).\
            first()
            
    @staticmethod
    def _update_privilege(id_class, granted, **kw):
        
        #logger = logging.getLogger('SapnsPrivileges._update_privilege')
        
        priv = SapnsPrivilege.get_privilege(id_class, **kw)
        if not kw.get('delete'):            
            
            if not priv:
                priv = SapnsPrivilege()
    
            priv.role_id = kw.get('id_role')
            priv.user_id = kw.get('id_user')
            priv.class_id = id_class
            priv.granted = granted
            
            dbs.add(priv)
            dbs.flush()
            
        elif priv:
            dbs.query(SapnsPrivilege).\
                filter(SapnsPrivilege.privilege_id == priv.privilege_id).\
                delete()
                
            dbs.flush()
        
        # reset cache
        _cache = cache.get_cache(SapnsPrivilege.CACHE_ID)
        
        def reset_user_cache(id_user):
            _key = '%d_%d' % (id_user, id_class)
            _cache.remove_value(key=_key)
        
        if kw.get('id_user'):
            # this user
            reset_user_cache(kw.get('id_user'))
            
        else:
            # all the users in this role
            role = dbs.query(SapnsRole).get(kw.get('id_role'))
            for user in role.users:
                reset_user_cache(user.user_id)
        
        return priv        
    
    @staticmethod 
    def add_privilege(id_class, **kw):
        return SapnsPrivilege._update_privilege(id_class, True, **kw)

    @staticmethod
    def remove_privilege(id_class, **kw):
        return SapnsPrivilege._update_privilege(id_class, False, **kw)
 
class SapnsAttrPrivilege(DeclarativeBase):
    
    __tablename__ = 'sp_attr_privileges'
    __table_args__ = (UniqueConstraint('id_user', 'id_attribute'),
                      UniqueConstraint('id_role', 'id_attribute'), {})
    
    attr_privilege_id = Column('id', Integer, primary_key=True, autoincrement=True)
    
    user_id = Column('id_user', Integer, 
                     ForeignKey('sp_users.id', 
                                onupdate='CASCADE', ondelete='CASCADE'))
    
    role_id = Column('id_role', Integer,
                     ForeignKey('sp_roles.id',
                                onupdate='CASCADE', ondelete='CASCADE'))
    
    attribute_id = Column('id_attribute', Integer, 
                          ForeignKey('sp_attributes.id',
                                     onupdate='CASCADE', ondelete='CASCADE'), 
                          nullable=False)
    
    access = Column(Unicode(15)) # denied, read-only, read/write
    
    ACCESS_DENIED = u'denied'
    ACCESS_READONLY = u'read-only'
    ACCESS_READWRITE = u'read/write'
    
    CACHE_ID = 'attrpriv_get_access'
    
    @staticmethod
    def get_privilege(id_attribute, **kw):
        return dbs.query(SapnsAttrPrivilege).\
            filter(and_(SapnsAttrPrivilege.role_id == kw.get('id_role'),
                        SapnsAttrPrivilege.user_id == kw.get('id_user'),
                        SapnsAttrPrivilege.attribute_id == id_attribute
                        )).\
            first()
    
    @staticmethod
    def get_access(id_user, id_attribute):

        def _get_access():
            _cmp = SapnsAttrPrivilege.cmp_access
            access = SapnsAttrPrivilege.ACCESS_DENIED
    
            # role_based
            for attr_priv in dbs.query(SapnsAttrPrivilege).\
                    join((SapnsRole,
                          SapnsRole.group_id == SapnsAttrPrivilege.role_id)).\
                    join((SapnsUserRole,
                          and_(SapnsUserRole.role_id == SapnsRole.group_id,
                               SapnsUserRole.user_id == id_user
                               ))).\
                    filter(SapnsAttrPrivilege.attribute_id == id_attribute):
                
                if _cmp(access, attr_priv.access) == -1:
                    access = attr_priv.access
                    
            # user based
            attr_priv = dbs.query(SapnsAttrPrivilege).\
                    filter(and_(SapnsAttrPrivilege.user_id == id_user,
                                SapnsAttrPrivilege.attribute_id == id_attribute)).\
                    first()
                
            if attr_priv and _cmp(access, attr_priv.access) == -1:
                access = attr_priv.access
                    
            return access
            
        _cache = cache.get_cache(SapnsAttrPrivilege.CACHE_ID)
        return _cache.get_value(key='%d_%d' % (id_user, id_attribute),
                                createfunc=_get_access, expiretime=1)

    @staticmethod
    def _update_privilege(id_attribute, access, **kw):
        
        priv = SapnsAttrPrivilege.get_privilege(id_attribute, **kw)
        if not priv:
            priv = SapnsAttrPrivilege()

        priv.role_id = kw.get('id_role')
        priv.user_id = kw.get('id_user')
        priv.attribute_id = id_attribute
        priv.access = access
        
        dbs.add(priv)
        dbs.flush()
        
        # reset cache
        _cache = cache.get_cache(SapnsAttrPrivilege.CACHE_ID)
        _cache2 = cache.get_cache(SapnsClass.CACHE_ID_ATTR)
        
        def reset_user_cache(id_user):
            _key = '%d_%d' % (id_user, id_attribute)
            _cache.remove_value(key=_key)
            
            _key2 = '%d_%d' % (priv.attribute.class_id, id_user)
            _cache2.remove_value(key=_key2)
        
        if kw.get('id_user'):
            # this user
            reset_user_cache(kw.get('id_user'))
            
        else:
            # all the users in this role
            role = dbs.query(SapnsRole).get(kw.get('id_role'))
            for user in role.users:
                reset_user_cache(user.user_id)
        
        return priv
        
    @staticmethod
    def add_privilege(id_attribute, access, **kw):
        return SapnsAttrPrivilege._update_privilege(id_attribute, access, **kw)
        
    @staticmethod
    def remove_privilege(id_attribute, **kw):
        if kw.get('remove'):
            dbs.query(SapnsAttrPrivilege).\
                filter(and_(SapnsAttrPrivilege.attribute_id == id_attribute,
                            SapnsAttrPrivilege.user_id == kw.get('id_user'),
                            SapnsAttrPrivilege.role_id == kw.get('id_role'),
                            )).\
                delete()
                
            dbs.flush()
            
        else:
            SapnsAttrPrivilege._update_privilege(id_attribute, SapnsAttrPrivilege.ACCESS_DENIED, **kw)
        
    @staticmethod
    def cmp_access(a1, a2):
        
        def value(a):
            if a == SapnsAttrPrivilege.ACCESS_READWRITE:
                return 3
            
            elif a == SapnsAttrPrivilege.ACCESS_READONLY:
                return 2
            
            elif a == SapnsAttrPrivilege.ACCESS_DENIED:
                return 1
            
        return cmp(value(a1), value(a2))

class SapnsPermission(Permission):
    """List of available actions in Sapns"""
    
    #__tablename__ = 'sp_actions'
    
    #action_id = Column('id', Integer, autoincrement=True, primary_key=True)

    #name = Column(Unicode(100), nullable=False)
    display_name = Column(Unicode(50), nullable=False)
    url = Column(Unicode(200))
    type = Column(Unicode(20))
    requires_id = Column(Boolean, default=True)
    
    # TODO: puede ser nulo? (nullable=False)
    class_id = Column('id_class', Integer, 
                      ForeignKey('sp_classes.id', 
                                 onupdate='CASCADE', ondelete='CASCADE'))
    # class_
    
    shortcuts = relation(SapnsShortcut, backref='permission')
    
    TYPE_NEW =     u'new'
    TYPE_EDIT =    u'edit'
    TYPE_DELETE =  u'delete'
    TYPE_DOCS =    u'docs'
    TYPE_REPORT =  u'report'
    TYPE_PROCESS = u'process'
    TYPE_LIST =    u'list'
    TYPE_OBJECT =  u'object'
    TYPE_GROUP =   u'group'
    
    # default URL
    URL_NEW =    u'/dashboard/new/'
    URL_EDIT =   u'/dashboard/edit/'
    URL_DELETE = u'/dashboard/delete/'
    URL_DOCS =   u'/dashboard/docs/'
    
    CACHE_ID = 'user_actions'
    
    def __unicode__(self):
        return u'<SapnsAction: "%s" type=%s>' % (self.permission_name, self.type)
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
#    def has_privilege(self, id_user):
#        return SapnsRolePermission.has_privilege(id_user, self.action_id)

class SapnsRolePermission(DeclarativeBase):

    __tablename__ = 'sp_role_permission'
    __table_args__ = (None, dict(useexisting=True))
    
    permission_id = Column('id_permission', Integer,
                           ForeignKey('sp_permission.id',
                                      onupdate="CASCADE", ondelete="CASCADE"),
                           primary_key=True)
                          
    role_id = Column('id_role', Integer, 
                     ForeignKey('sp_roles.id',
                                onupdate="CASCADE", ondelete="CASCADE"), 
                     primary_key=True)
    
    @staticmethod
    def has_permission(id_role, id_permission):
        return dbs.query(SapnsRolePermission).\
            filter(and_(SapnsRolePermission.role_id == id_role,
                        SapnsRolePermission.permission_id == id_permission)).\
            first() != None

class SapnsView(DeclarativeBase):
    """Views in Sapns"""
    
    __tablename__ = 'sp_views'
    
    view_id = Column('id', Integer, autoincrement=True, primary_key=True)
    title = Column(Unicode(200), nullable=False)
    code = Column(Unicode(30), nullable=False)

class SapnsViewColumn(DeclarativeBase):
    """View columns in Sapns"""
    
    __tablename__ = 'sp_view_columns'
    
    column_id = Column('id', Integer, autoincrement=True, primary_key=True)
    title = Column(Unicode(30), nullable=False)
    definition = Column(Text, nullable=False)
    alias = Column(Unicode(100), nullable=False)
    order = Column(Integer)
    
    text_align = Column(Unicode(10))
    width = Column(Integer)
    
    view_id = Column('id_view', Integer, 
                     ForeignKey('sp_views.id',
                                onupdate='CASCADE', ondelete='CASCADE'), 
                     nullable=False)
    
    # columns (SapnsViewColumn)
    # relations (SapnsViewRelation)
    # filters (SapnsViewFilter)
    # orders (SapnsViewOrder)
    
SapnsView.columns = \
    relation(SapnsViewColumn, 
             backref='view', 
             primaryjoin=SapnsView.view_id == SapnsViewColumn.view_id)
    
class SapnsViewRelation(DeclarativeBase):
    """View joins in Sapns"""
    
    __tablename__ = 'sp_view_relations'
    
    relation_id = Column('id', Integer, autoincrement=True, primary_key=True)
    
    name = Column(Unicode(30), nullable=False)
    alias = Column(Unicode(100), nullable=False)
    condition = Column(Text)
    is_inner = Column(Boolean, default=False)
    
    view_id = Column('id_view', Integer, 
                     ForeignKey('sp_views.id',
                                onupdate='CASCADE', ondelete='CASCADE'), 
                     nullable=False)
    
SapnsView.relations = \
    relation(SapnsViewRelation, 
             backref='view', 
             primaryjoin=SapnsView.view_id == SapnsViewRelation.view_id)
    
class SapnsViewFilter(DeclarativeBase):
    """'Where' clauses in Sapns views"""
    
    __tablename__ = 'sp_view_filters'

    filter_id = Column('id', Integer, autoincrement=True, primary_key=True)
    
    definition = Column(Text)
    active = Column(Boolean)

    view_id = Column('id_view', Integer, 
                     ForeignKey('sp_views.id',
                                onupdate='CASCADE', ondelete='CASCADE'), 
                     nullable=False)
    
SapnsView.filters = \
    relation(SapnsViewFilter, 
             backref='view', 
             primaryjoin=SapnsView.view_id == SapnsViewFilter.view_id)

class SapnsViewOrder(DeclarativeBase):
    """Sort order in Sapns views"""
    
    __tablename__ = 'sp_view_order'
    
    order_id = Column('id', Integer, autoincrement=True, primary_key=True)
    definition = Column(Text)
    sort_order = Column(Integer)

    view_id = Column('id_view', Integer, 
                     ForeignKey('sp_views.id',
                                onupdate='CASCADE', ondelete='CASCADE'), 
                     nullable=False)
    
SapnsView.orders = \
    relation(SapnsViewOrder, 
             backref='view', 
             primaryjoin=SapnsView.view_id == SapnsViewOrder.view_id)
    
class SapnsReport(DeclarativeBase):
    """Sapns reports (probably in JasperReports, for starters)"""
    
    __tablename__ = 'sp_reports'
    
    report_id = Column('id', Integer, autoincrement=True, primary_key=True)
    
    code = Column(Unicode(50), nullable=False, unique=True)
    name = Column(Unicode(200), nullable=False, unique=True)
    
    description = Column(Text)

class SapnsReportParam(DeclarativeBase):
    """Sapns param list: so we know what to request from the user when we launch the report"""
    
    __tablename__ = 'sp_report_parameters' 
    
    reportparam_id = Column('id', Integer, autoincrement=True, primary_key=True)
    
    name = Column(Unicode(200), nullable=False)
    
    class_id = Column('id_class', Integer, 
                      ForeignKey('sp_classes.id',
                                 onupdate='CASCADE', ondelete='CASCADE'), 
                      nullable=False)
    
    default_value = Column(Unicode(200))
    
    sort_order = Column(Integer)
    expression = Column(Text)
    
    report_id = Column('id_report', Integer, 
                       ForeignKey('sp_reports.id',
                                  onupdate='CASCADE', ondelete='CASCADE'), 
                       nullable=False)
    
SapnsReport.params = \
    relation(SapnsReportParam, 
             backref='report', 
             primaryjoin=SapnsReport.report_id == SapnsReportParam.report_id)
    
class SapnsMessage(DeclarativeBase):
    """Internal messages between users"""
    
    __tablename__ = 'sp_messages'
    
    message_id = Column('id', Integer, autoincrement=True, primary_key=True)
    user_from_id = Column('id_user_from', Integer, 
                         ForeignKey('sp_users.id',
                                    onupdate='CASCADE', ondelete='SET NULL'))
    
    created_date = Column(Date, default=dt.date.today())
    created_time = Column(Time, default=dt.datetime.now().time())
    subject = Column(Unicode(100), nullable=False)
    body = Column(Text)

class SapnsMessageTo(DeclarativeBase):
    
    __tablename__ = 'sp_message_to'
    __table_args__ = (UniqueConstraint('id_message', 'id_user_to'), {})
    
    messageto_id = Column('id', Integer, primary_key=True, autoincrement=True)
    
    message_id = Column('id_message', Integer, 
                        ForeignKey('sp_messages.id',
                                   onupdate='CASCADE', ondelete='CASCADE'),
                        )
    
    user_to_id = Column('id_user_to', Integer,
                        ForeignKey('sp_users.id',
                                   onupdate='CASCADE', ondelete='CASCADE'),
                        )
    
    is_read = Column(Boolean, default=False)
    
class SapnsRepo(DeclarativeBase):
    
    __tablename__ = 'sp_repos'
    
    repo_id = Column('id', Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(50), nullable=False)
    path = Column(Unicode(255))
    
    docs = relation('SapnsDoc', backref='repo')
    
    def abs_path(self):
        REPO_BASE_PATH = config.get('app.repo_base')
        return os.path.join(REPO_BASE_PATH, self.path)
    
    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.path)
    
    def __repr__(self):
        return unicode(self).encode('utf-8')
    
class SapnsDoc(DeclarativeBase):
    
    __tablename__ = 'sp_docs'
    
    doc_id = Column('id', Integer, primary_key=True, autoincrement=True)
    title = Column(Unicode(200), nullable=False)
    filename = Column(Unicode(200))
    
    repo_id = Column('id_repo', Integer, 
                     ForeignKey('sp_repos.id',
                                onupdate='CASCADE', ondelete='SET NULL'))
    # repo
    
    author_id = Column('id_author', Integer,
                       ForeignKey('sp_users.id',
                                  onupdate='CASCADE', ondelete='SET NULL'))
    # authors
    
    doctype_id = Column('id_doctype', Integer, 
                        ForeignKey('sp_doctypes.id',
                                   onupdate='CASCADE', ondelete='SET NULL'))
    # doctype
    
    docformat_id = Column('id_docformat', Integer,
                          ForeignKey('sp_docformats.id',
                                     onupdate='CASCADE', ondelete='RESTRICT'))
    # docformat
    
    assigned_docs = relation('SapnsAssignedDoc', backref='doc')
    
    def __unicode__(self):
        return u'%s' % self.title
    
    def __repr__(self):
        return unicode(self).encode('utf-8')
    
    def title_as_filename(self):
        t = (self.title or _('NO_TITLE'))
        pat = re.compile(r'[^a-z0-9_\-.]', re.I)
        return re.sub(pat, '_', t).encode('utf-8')
    
    def register(self, cls, object_id):
        """
        IN
          cls        <int>/<unicode>/<str>
          object_id  <int>
        """
        
        if isinstance(cls, int):
            cls = dbs.query(SapnsClass).get(cls)
            
        elif isinstance(cls, (str, unicode,)):
            cls = SapnsClass.by_name(cls, parent=False)

        # assign doc to object/class
        ad = SapnsAssignedDoc()
        ad.doc_id = self.doc_id
        ad.class_id = cls.class_id
        ad.object_id = object_id
        
        dbs.add(ad)
        dbs.flush()
    
    @staticmethod
    def delete_doc(id_doc):
        """
        IN
          id_doc  <int>
        """
        
        id_doc = int(id_doc)
        doc = dbs.query(SapnsDoc).get(id_doc)
        
        # remove file from disk
        SapnsDoc.remove_file(doc.repo_id, doc.filename)
        
        # remove doc
        dbs.query(SapnsDoc).filter(SapnsDoc.doc_id == id_doc).delete()
        dbs.flush()
    
    @staticmethod
    def upload(f, id_repo):
        """
        IN
          f        <file>
          id_repo  <int>
          
        OUT
          {uploaded_file: <str>,
           file_name:     <str>,
           file_size:     <int>}
        """
        
        import hashlib as hl
        import random
        
        # get repo
        repo = dbs.query(SapnsRepo).get(id_repo)
        if not repo:
            raise Exception(_('Repo [%d] was not found') % id_repo)
        
        repo_path = repo.abs_path()
        
        # calculate random name for the new file
        def _file_path():
            
            # create hash
            s256 = hl.sha256()
            
            random.seed()
            s256.update('%s%6.6d' % (f.filename.encode('utf-8'), random.randint(0, 999999)))
            
            file_name = s256.hexdigest()
            return os.path.join(repo_path, file_name), file_name
        
        while True:
            file_path, file_name = _file_path()
            # does it exist???
            if not os.access(file_path, os.F_OK):
                break
        
        f.file.seek(0)
        with file(file_path, 'wb') as fu:
            fu.write(f.file.read())
            
        return dict(uploaded_file=f.filename,
                    file_name=file_name,
                    file_size=f.file.tell())
        
    @staticmethod
    def download(id_doc):
        """
        IN
          id_doc  <int>
          
        OUT
          (<content>, <mime type>, <file name>,)
        """
        
        import mimetypes
        
        doc = dbs.query(SapnsDoc).get(id_doc)
        if not doc:
            # TODO: document does not exist
            pass
        
        content = ''
        f = file(os.path.join(doc.repo.abs_path(), doc.filename), 'rb')
        try:
            content = f.read()
        
        finally:
            f.close()
            
        file_name = ('%s.%s' % (doc.title_as_filename(), doc.docformat.extension)).encode('utf-8')
            
        mt = doc.docformat.mime_type
        if not mt:
            mt = mimetypes.guess_type(file_name)[0]
            
        return content, mt, file_name
    
    @staticmethod
    def remove_file(id_repo, file_name):

        repo = dbs.query(SapnsRepo).get(id_repo)
        if not repo:
            raise Exception(_('Repo [%d] was not found') % id_repo)
        
        path_file = os.path.join(repo.abs_path(), file_name) 
        if os.access(path_file, os.F_OK):
            os.remove(path_file)


class SapnsDocType(DeclarativeBase):
    
    __tablename__ = 'sp_doctypes'
    
    doctype_id = Column('id', Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(80), nullable=False)
    description = Column(Text)
    
    docs = relation('SapnsDoc', backref='doctype')
    
    def __unicode__(self):
        return u'%s' % self.description
    
    def __repr__(self):
        return unicode(self).encode('utf-8')
    
class SapnsDocFormat(DeclarativeBase):
    
    __tablename__ = 'sp_docformats'
    
    docformat_id = Column('id', Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(80), nullable=False)
    extension = Column(Unicode(5), nullable=False)
    mime_type = Column(Unicode(30), nullable=False)
    description = Column(Text)
    
    docs = relation('SapnsDoc', backref='docformat')
    
class SapnsAssignedDoc(DeclarativeBase):
    
    __tablename__ = 'sp_assigned_docs'
    
    assigneddoc_id = Column('id', Integer, primary_key=True, autoincrement=True)
    
    class_id = Column('id_class', Integer, 
                      ForeignKey('sp_classes.id',
                                 onupdate='CASCADE', ondelete='SET NULL'))
    
    doc_id = Column('id_doc', Integer, 
                    ForeignKey('sp_docs.id',
                               onupdate='CASCADE', ondelete='CASCADE'))
    # doc
    
    object_id = Column(Integer)
    
class SapnsUpdates(DeclarativeBase):
    
    __tablename__ = 'sp_updates'
    
    update_id = Column('id', Integer, primary_key=True)
    code = Column(Unicode(50), nullable=False)
    description = Column(Text)
    exec_date = Column(DateTime)
    
    @staticmethod
    def by_code(code):
        return dbs.query(SapnsUpdates).\
            filter(SapnsUpdates.code == code).first()
            
class SapnsLog(DeclarativeBase):
    
    __tablename__ = 'sp_logs'
    
    log_id = Column('id', BigInteger, primary_key=True)
    table_name = Column(Unicode(100))
    row_id = Column(BigInteger)
    when_ = Column(DateTime, default=dt.datetime.now())
    who = Column(Integer, 
                 ForeignKey('sp_users.id',
                            onupdate='CASCADE', ondelete='SET NULL'))
    what = Column(Unicode(100))
    description = Column(Text)
    auto = Column(Boolean, default=False)
    
    @staticmethod
    def register(**kw):
        """
        IN
          table_name   <unicode>
          row_id       <int>
          when_        <datetime>
          who          <int>
          what         <unicode>
          description  <unicode>
        """
        
        #logger = logging.getLogger('SapnsLog.register')
        #logger.info(kw)
        
        log = SapnsLog()
        
        create_log = True
        if kw.get('table_name'):
            cls = dbs.query(SapnsClass).\
                filter(and_(SapnsClass.name == kw['table_name'],
                            SapnsClass.is_logged,
                            )).\
                first()

            create_log = cls != None
                
        if create_log:
            for k, v in kw.iteritems():
                setattr(log, k, v)
                
            dbs.add(log)
            dbs.flush()