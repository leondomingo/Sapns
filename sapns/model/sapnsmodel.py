# -*- coding: utf-8 -*-

"""Sapns basic data model"""

import os
import sys
import shutil
import datetime as dt

from pylons.i18n import ugettext as _

from tg import config
from pylons import cache

from sqlalchemy import MetaData, Table, ForeignKey, Column, UniqueConstraint, DefaultClause
from sqlalchemy.sql.expression import and_, select, alias, desc, bindparam
from sqlalchemy.types import Unicode, Integer, String, Boolean, DateTime, Date,\
    Time, Text
from sqlalchemy import MetaData, Table
from sqlalchemy.orm import relation, synonym

from sapns.model import DeclarativeBase, metadata, DBSession as dbs
from sapns.model.auth import User

import logging
from neptuno.util import datetostr
from sqlalchemy.exc import NoSuchTableError

__all__ = ['SapnsAction', 'SapnsAttrPrivilege', 'SapnsAttribute',
           'SapnsClass', 'SapnsPrivilege', 'SapnsReport', 'SapnsReportParam',
           'SapnsShortcut', 'SapnsUser', 'SapnsView', 'SapnsViewColumn',
           'SapnsViewFilter', 'SapnsViewOrder', 'SapnsViewRelation',
           'SapnsMessage', 'SapnsMessageTo',
           'SapnsRepo', 'SapnsDoc', 'SapnsDocType', 'SapnsAssignedDoc',
          ]

# inherited class from "User"
class SapnsUser(User):
    
    def get_dashboard(self):
        return dbs.query(SapnsShortcut).\
            filter(and_(SapnsShortcut.user_id == self.user_id,
                        SapnsShortcut.parent_id == None)).\
            first()
    
    def get_dataexploration(self):
        return dbs.query(SapnsShortcut).\
            filter(and_(SapnsShortcut.parent_id == self.get_dashboard().shortcut_id,
                        SapnsShortcut.order == 0,
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
            for sc, ac, cl in dbs.query(SapnsShortcut, SapnsAction, SapnsClass).\
                    outerjoin((SapnsAction,
                               SapnsAction.action_id == SapnsShortcut.action_id)).\
                    outerjoin((SapnsClass, 
                               SapnsClass.class_id == SapnsAction.class_id)).\
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
                sc_copy.action_id = sc.action_id
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
                
        except Exception, e:
            logger.error(e)
            
    def from_list(self, title, url):
        
        # new action
        action_link = SapnsAction()
        action_link.class_id = None
        action_link.type = SapnsAction.TYPE_OBJECT
        action_link.name = title
        action_link.url = url
        
        dbs.add(action_link)
        dbs.flush()
        
        # new shortcut
        sc_link = SapnsShortcut()
        sc_link.action_id = action_link.action_id
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
    
    def has_privilege(self, cls):
        
        def _has_privilege():
            priv = dbs.query(SapnsPrivilege).\
                join((SapnsClass,
                      SapnsClass.class_id == SapnsPrivilege.class_id)).\
                filter(and_(SapnsPrivilege.user_id == self.user_id,
                            SapnsClass.name == cls)).\
                first()
                
            return priv != None
        
        _cache = cache.get_cache('user_has_privilege')
        return _cache.get_value(key='%s_%d' % (cls, self.user_id),
                                createfunc=_has_privilege, expiretime=3600)
    
    def attr_privilege(self, id_attribute):
        
        return dbs.query(SapnsAttrPrivilege).\
            filter(and_(SapnsAttrPrivilege.user_id == self.user_id,
                        SapnsAttrPrivilege.attribute_id == id_attribute,
                        )).\
            first()
    
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
    
    action_id = Column('id_action', Integer, 
                       ForeignKey('sp_actions.id', 
                                  onupdate='CASCADE', ondelete='SET NULL')) #, nullable=False)
    
    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u'<Shortcut: "%s" user=%s, action=%s>' % \
            (self.title, self.user, self.action or '')
    
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
            new_sc.action_id = sc.action_id
            
        else:
            new_sc = dbs.query(SapnsShortcut).get(id_shortcut)
        
        new_sc.parent_id = self.shortcut_id
        new_sc.order = self.next_order()
        
        dbs.add(new_sc)
        dbs.flush()
        
    REORDER_TYPE_UP = 'up'
    REORDER_TYPE_DOWN = 'down'
        
    def reorder(self, type='up'):
        
        logger = logging.getLogger('SapnsShortcut.reorder')
        logger.info(unicode(self))
        
        def _reorder(this, that):
            aux = that.order
            that.order = this.order
            this.order = aux
            
            dbs.add(this)
            dbs.add(that)
            dbs.flush()
            
        if type == SapnsShortcut.REORDER_TYPE_UP:
            if self.order > 0:
                next_sc = self.parent.by_order(self.order-1, -1)
            
            else:
                raise Exception('It is not possible to go upper')
            
        elif type == SapnsShortcut.REORDER_TYPE_DOWN:
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
    
    # attributes (SapnsAttribute)
    
    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.title)
    
    def __repr__(self):
        return unicode(self).encode('utf-8')
    
    @staticmethod
    def by_name(class_name):
        """
        Returns the SapnsClass whose name is "class_name"
        IN
          class_name  <unicode>
          
        OUT
          <SapnsClass>
        """
        return dbs.query(SapnsClass).\
            filter(SapnsClass.name == class_name).\
            first()
                
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
        _title = SapnsClass.ObjectTitle(class_name).title(id_object)
        
        if not _title:
            cls = SapnsClass.by_name(class_name)
            _title = '[%s: %s]' % (cls.title, id_object)
            
        return _title
    
    def sorted_actions(self):
        """
        Returns a list of actions associated with this class.
        
        OUT
          [{"title":      <unicode>, 
            "url":        <unicode>, 
            "require_id": <bool>, 
            "type":       <unicode>}, ...]
        """
        
        def _sorted_actions():
            actions = []
            for ac in dbs.query(SapnsAction).\
                    filter(and_(SapnsAction.class_id == self.class_id,
                                SapnsAction.type != SapnsAction.TYPE_LIST,
                                )).\
                    all():
                
                url = ac.url
                if url and url[-1] != '/':
                    url += '/'
                    
                require_id = True
                if ac.type == SapnsAction.TYPE_NEW:
                    url = SapnsAction.URL_NEW
                    require_id = False
                
                elif ac.type == SapnsAction.TYPE_EDIT:
                    url = SapnsAction.URL_EDIT
                
                elif ac.type == SapnsAction.TYPE_DELETE:
                    url = SapnsAction.URL_DELETE
                
                actions.append(dict(title=_(ac.name), type=ac.type, 
                                    url=url, require_id=require_id))
        
            return actions
        
        _cache = cache.get_cache('sorted_actions')
        return _cache.get_value(key=self.class_id, createfunc=_sorted_actions,
                                expiretime=3600)
    
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
        
        def _get_attributes():
            return dbs.query(SapnsAttribute, SapnsAttrPrivilege).\
                    join((SapnsAttrPrivilege, 
                          and_(SapnsAttrPrivilege.user_id == id_user,
                               SapnsAttrPrivilege.attribute_id == SapnsAttribute.attribute_id))).\
                    filter(and_(SapnsAttribute.class_id == self.class_id,
                                SapnsAttribute.visible == True)).\
                    order_by(SapnsAttribute.insertion_order)
            
        _cache = cache.get_cache('class_get_attributes')
        return _cache.get_value(key='%d_%d' % (self.class_id, id_user),
                                createfunc=_get_attributes, expiretime=3600)
        

class SapnsAttribute(DeclarativeBase):
    
    """List of sapns columns in tables"""
    
    __tablename__ = 'sp_attributes'
    __table_args__ = (UniqueConstraint('name', 'id_class'), {})

    attribute_id = Column('id', Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(60), nullable=False)
    title = Column(Unicode(100), nullable=False)
    
    class_id = Column('id_class', Integer, 
                      ForeignKey('sp_classes.id', 
                                 onupdate='CASCADE', ondelete='CASCADE'), 
                      nullable=False)
    
    related_class_id = Column('id_related_class', Integer, 
                              ForeignKey('sp_classes.id',
                                         onupdate='CASCADE', ondelete='SET NULL'))
    
    TYPE_INTEGER = 'int'
    TYPE_BOOLEAN = 'bool'
    TYPE_FLOAT = 'float'
    TYPE_STRING = 'str'
    TYPE_MEMO = 'memo'
    TYPE_DATE = 'date'
    TYPE_TIME = 'time'
    TYPE_DATETIME = 'datetime'
    TYPE_IMAGE = 'img'
    
    type = Column(Unicode(20), nullable=False)
    required = Column(Boolean, DefaultClause('false'), default=False)
    reference_order = Column(Integer)
    insertion_order = Column(Integer)
    visible = Column(Boolean, DefaultClause('true'), default=True)
    #is_collection = Column(Boolean, DefaultClause('false'), default=False)
    
    def __unicode__(self):
        return u'<%s> %s %s (%s)' % (unicode(self.class_), self.title, self.name)
    
    def __repr__(self):
        return unicode(self).encode('utf-8')
    
SapnsClass.attributes = \
    relation(SapnsAttribute,
             backref='class_',
             primaryjoin=SapnsClass.class_id == SapnsAttribute.class_id)
    
SapnsClass.related_attributes = \
    relation(SapnsAttribute,
             backref='related_class',
             primaryjoin=SapnsClass.class_id == SapnsAttribute.related_class_id)

class SapnsPrivilege(DeclarativeBase):
    
    __tablename__ = 'sp_privileges'
    __table_args__ = (UniqueConstraint('id_user', 'id_class'), {})
    
    privilege_id = Column('id', Integer, primary_key=True, autoincrement=True)
    
    user_id = Column('id_user', Integer, 
                     ForeignKey('sp_users.id',
                                onupdate='CASCADE', ondelete='CASCADE'),
                     nullable=False)
    
    class_id = Column('id_class', Integer, 
                      ForeignKey('sp_classes.id', 
                                 onupdate='CASCADE', ondelete='CASCADE'), 
                      nullable=False)
    
    @staticmethod
    def has_privilege(id_user, id_class):
        priv = dbs.query(SapnsPrivilege).\
                filter(and_(SapnsPrivilege.user_id == id_user,
                            SapnsPrivilege.class_id == id_class,
                            )).\
                first()
                
        return priv != None
    
    @staticmethod
    def add_privilege(id_user, id_class):
        priv = SapnsPrivilege()
        priv.user = id_user
        priv.class_ = id_class
        
        dbs.add(priv)
        dbs.flush()
        
    @staticmethod
    def remove_privilege(id_user, id_class):
        dbs.query(SapnsPrivilege).\
            filter(and_(SapnsPrivilege.user_id == id_user,
                        SapnsPrivilege.class_id == id_class,
                        )).\
            delete()
            
        dbs.flush()

class SapnsAttrPrivilege(DeclarativeBase):
    
    __tablename__ = 'sp_attr_privileges'
    __table_args__ = (UniqueConstraint('id_user', 'id_attribute'), {})
    
    attr_privilege_id = Column('id', Integer, primary_key=True, autoincrement=True)
    
    user_id = Column('id_user', Integer, 
                     ForeignKey('sp_users.id', 
                                onupdate='CASCADE', ondelete='CASCADE'), 
                     nullable=False)
    
    attribute_id = Column('id_attribute', Integer, 
                          ForeignKey('sp_attributes.id',
                                     onupdate='CASCADE', ondelete='CASCADE'), 
                          nullable=False)
    
    access = Column(Unicode(15)) # denied, read-only, read/write
    
    ACCESS_DENIED = 'denied'
    ACCESS_READONLY = 'read-only'
    ACCESS_READWRITE = 'read/write'
    
    @staticmethod
    def get_privilege(id_user, id_attribute):
        
        return dbs.query(SapnsAttrPrivilege).\
            filter(and_(SapnsAttrPrivilege.user_id == id_user,
                        SapnsAttrPrivilege.attribute_id == id_attribute
                        )).\
            first()
    
    @staticmethod
    def get_access(id_user, id_attribute):
        
        def _get_access():
        
            priv = SapnsAttrPrivilege.get_privilege(id_user, id_attribute)
            if priv is None:
                return SapnsAttrPrivilege.ACCESS_DENIED
            
            else:
                return priv.access
            
        _cache = cache.get_cache('attrpriv_get_access')
        return _cache.get_value(key='%d_%d' % (id_user, id_attribute),
                                createfunc=_get_access, expiretime=3600)
        
    @staticmethod
    def add_privilege(id_user, id_attribute, access):
        
        priv = SapnsAttrPrivilege.get_privilege(id_user, id_attribute)
        if priv is None:
            priv = SapnsAttrPrivilege()
            priv.user_id = id_user
            priv.attribute_id = id_attribute
            priv.access = access
            
        else:
            priv.access = access
            
        dbs.add(priv)
        dbs.flush()
        
    @staticmethod
    def remove_privilege(id_user, id_attribute):
        dbs.query(SapnsAttrPrivilege).\
            filter(and_(SapnsAttrPrivilege.user_id == id_user,
                        SapnsAttrPrivilege.attribute_id == id_attribute,
                        )).\
            delete()
            
        dbs.flush()

class SapnsAction(DeclarativeBase):
    """List of available actions in Sapns"""
    
    __tablename__ = 'sp_actions'
    
    action_id = Column('id', Integer, autoincrement=True, primary_key=True)

    name = Column(Unicode(100), nullable=False)
    url = Column(Unicode(200)) #, nullable=False)
    type = Column(Unicode(20), nullable=False)
    
    # TODO: puede ser nulo? (nullable=False)
    class_id = Column('id_class', Integer, 
                      ForeignKey('sp_classes.id', 
                                 onupdate='CASCADE', ondelete='CASCADE'))
    
    TYPE_NEW = 'new'
    TYPE_EDIT = 'edit'
    TYPE_DELETE = 'delete'
    TYPE_REPORT = 'report'
    TYPE_PROCESS = 'process'
    TYPE_LIST = 'list'
    TYPE_OBJECT = 'object'
    TYPE_GROUP = 'group'
    
    # default URL
    URL_NEW = '/dashboard/new'
    URL_EDIT = '/dashboard/edit'
    URL_DELETE = '/dashboard/delete'
    
    def __unicode__(self):
        return u'<SapnsAction: "%s" type=%s>' % (self.name, self.type)
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
SapnsAction.shortcuts = \
    relation(SapnsShortcut,
             backref='action',
             primaryjoin=SapnsAction.action_id == SapnsShortcut.action_id)
    
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
    
    author_id = Column('id_author', Integer,
                       ForeignKey('sp_users.id',
                                  onupdate='CASCADE', ondelete='SET NULL'))
    
    doctype_id = Column('id_doctype', Integer, 
                        ForeignKey('sp_doctypes.id',
                                   onupdate='CASCADE', ondelete='SET NULL'))
    
    docformat_id = Column('id_docformat', Integer,
                          ForeignKey('sp_docformats.id',
                                     onupdate='CASCADE', ondelete='RESTRICT'))
    
    def __unicode__(self):
        return u'%s' % self.title
    
    def __repr__(self):
        return unicode(self).encode('utf-8')

SapnsRepo.docs = \
    relation(SapnsDoc,
             backref='repo', 
             primaryjoin=SapnsRepo.repo_id == SapnsDoc.repo_id)
    
SapnsUser.authored_docs = \
    relation(SapnsDoc,
             backref='author',
             primaryjoin=SapnsUser.user_id == SapnsDoc.author_id)
    
class SapnsDocType(DeclarativeBase):
    
    __tablename__ = 'sp_doctypes'
    
    doctype_id = Column('id', Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(80), nullable=False)
    description = Column(Text)
    
    docs = relation(SapnsDoc, 
                    backref='doctype', 
                    primaryjoin=doctype_id == SapnsDoc.doctype_id)
    
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
    
    docs = relation(SapnsDoc, backref='docformat',
                    primaryjoin=docformat_id == SapnsDoc.docformat_id)
    
class SapnsAssignedDoc(DeclarativeBase):
    
    __tablename__ = 'sp_assigned_docs'
    
    assigneddoc_id = Column('id', Integer, primary_key=True, autoincrement=True)
    
    class_id = Column('id_class', Integer, 
                      ForeignKey('sp_classes.id',
                                 onupdate='CASCADE', ondelete='SET NULL'))
    
    doc_id = Column('id_doc', Integer, 
                    ForeignKey('sp_docs.id',
                               onupdate='CASCADE', ondelete='CASCADE'))
    
    object_id = Column(Integer)
    
SapnsDoc.assigned_docs = \
    relation(SapnsAssignedDoc,
             backref='doc',
             primaryjoin=SapnsDoc.doc_id == SapnsAssignedDoc.doc_id)