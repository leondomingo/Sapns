# -*- coding: utf-8 -*-
"""
  Modelo de datos básico de sapns 
"""
import os
import sys
from datetime import datetime

from pylons.i18n import ugettext as _

from sqlalchemy import ForeignKey, Column, UniqueConstraint, DefaultClause
from sqlalchemy.types import Unicode, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relation, synonym

from sapns.model import DeclarativeBase, metadata, DBSession
from sapns.model.auth import User
from sqlalchemy.sql.expression import and_

import logging

__all__ = ['SapnsAction', 'SapnsAttrPrivilege', 'SapnsAttribute',
           'SapnsClass', 'SapnsPrivilege', 'SapnsReport', 'SapnsReportParam',
           'SapnsShortcut', 'SapnsUser', 'SapnsView', 'SapnsViewColumn',
           'SapnsViewFilter', 'SapnsViewOrder', 'SapnsViewRelation',
          ]

# inherited class
class SapnsUser(User):
    
    def get_dashboard(self):
        dboard = DBSession.query(SapnsShortcut).\
                    filter(and_(SapnsShortcut.user_id == self.user_id,
                                SapnsShortcut.parent_id == None)).\
                    first()
                    
        return dboard
    
    def get_shortcuts(self, id_parent=None):
        
        logger = logging.getLogger('SapnsUser.get_shortcuts')

        if not id_parent:
            id_parent = self.get_dashboard().shortcut_id
            
        shortcuts = []
        for sc, ac, cl in DBSession.query(SapnsShortcut, 
                                          SapnsAction,
                                          SapnsClass).\
                outerjoin((SapnsAction,
                           SapnsAction.action_id == SapnsShortcut.action_id)).\
                outerjoin((SapnsClass, SapnsClass.class_id == SapnsAction.class_id)).\
                filter(and_(SapnsShortcut.user_id == self.user_id,
                            SapnsShortcut.parent_id == id_parent)).\
                order_by(SapnsShortcut.order).\
                all():
            
            logger.info('Getting shortcut "%s"' % sc.title)
            url = ''
            type_ = ''
            class_ = ''
            if ac:
                url = ac.url
                type_ = ac.type
                
                if cl:
                    class_ = cl.name 
                            
            shortcuts.append(dict(url=url, 
                                  title=sc.title,
                                  action_type=type_,
                                  cls=class_,
                                  parent=sc.parent_id, 
                                  id=sc.shortcut_id))
        
        return shortcuts

class SapnsShortcut(DeclarativeBase):
    """
    Shortcuts sapns base table
    """

    __tablename__ = 'sp_shortcuts'

    shortcut_id = Column('id', Integer, autoincrement=True, primary_key=True)
    title = Column(Unicode(50))
    order = Column(Integer)
    parent_id = Column('id_parent_shortcut', Integer, ForeignKey('sp_shortcuts.id'))
    
    user_id = Column('id_user', Integer, ForeignKey('sp_users.id'), nullable=False)
    action_id = Column('id_action', Integer, ForeignKey('sp_actions.id')) #, nullable=False)
    
    def __repr__(self):
        return ('<Shortcut: user=%s, action=%s>' % self.user, self.action).encode('utf-8')

    def __unicode__(self):
        return u'<Shortcut: user=%s, action=%s>' % (self.user, self.action)
    

# TODO: 1-to-1 autoreference relation
SapnsShortcut.children = \
    relation(SapnsShortcut,
             backref='parent',
             uselist=False,
             remote_side=[SapnsShortcut.shortcut_id],
             primaryjoin=SapnsShortcut.shortcut_id == SapnsShortcut.parent_id)

class SapnsClass(DeclarativeBase):
    """
    List of sapns tables
    """

    __tablename__ = 'sp_classes'
    __table_args__ = (UniqueConstraint('name'), {})
    
    class_id = Column('id', Integer, autoincrement=True, primary_key=True)
    
    name = Column(Unicode(50), nullable=False)
    title = Column(Unicode(100), nullable=False)
    description = Column(String)
    
    # attributes (SapnsAttribute)
    
    def sorted_actions(self):
        
        actions = []
        for ac in DBSession.query(SapnsAction).\
                filter(and_(SapnsAction.class_id == self.class_id,
                            SapnsAction.type != SapnsAction.TYPE_LIST,
                            )).\
                all():
            
            url = ac.url
            require_id = True
            if ac.type == SapnsAction.TYPE_NEW:
                url = SapnsAction.URL_NEW
                require_id = False
            
            elif ac.type == SapnsAction.TYPE_EDIT:
                url = SapnsAction.URL_EDIT
            
            elif ac.type == SapnsAction.TYPE_DELETE:
                url = SapnsAction.URL_DELETE
            
            actions.append(dict(title=_(ac.name), url=url, require_id=require_id))
    
        return actions
    
class SapnsAttribute(DeclarativeBase):
    
    """
    List of sapns columns in tables
    """
    
    __tablename__ = 'sp_attributes'
    __table_args__ = (UniqueConstraint('name', 'id_class'), {})

    attribute_id = Column('id', Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(60), nullable=False)
    title = Column(Unicode(100), nullable=False)
    
    class_id = Column('id_class', Integer, ForeignKey('sp_classes.id'), nullable=False)
    
    type_ = Column('type', Unicode(20), nullable=False)
    reference_order = Column(Integer)
    insertion_order = Column(Integer)
    is_collection = Column(Boolean, DefaultClause('false'), default=False)
    
SapnsClass.attributes = \
    relation(SapnsAttribute,
             backref='class_',
             primaryjoin=SapnsClass.class_id == SapnsAttribute.class_id)

class SapnsPrivilege(DeclarativeBase):
    
    __tablename__ = 'sp_privilege'
    
    user_id = Column('id_user', Integer, ForeignKey('sp_users.id'), 
                     primary_key=True, nullable=False)
    class_id = Column('id_class', Integer, ForeignKey('sp_classes.id'), 
                      primary_key=True, nullable=False)
    
    @staticmethod
    def has_privilege(id_user, id_class):
        priv = DBSession.query(SapnsPrivilege).\
                filter(and_(SapnsPrivilege.user_id == id_user,
                            SapnsPrivilege.class_id == id_class,
                            ))
                
        return priv != None
    
    @staticmethod
    def add_privilege(id_user, id_class):
        priv = SapnsPrivilege()
        priv.user = id_user
        priv.class_ = id_class
        
        DBSession.add(priv)
        DBSession.flush()
        
    @staticmethod
    def remove_privilege(id_user, id_class):
        DBSession.query(SapnsPrivilege).\
            filter(and_(SapnsPrivilege.user_id == id_user,
                        SapnsPrivilege.class_id == id_class,
                        )).\
            delete()
            
        DBSession.flush()

class SapnsAttrPrivilege(DeclarativeBase):
    
    __tablename__ = 'sp_attr_privilege'
    
    user_id = Column('id_user', Integer, ForeignKey('sp_users.id'), 
                     primary_key=True, nullable=False)
    attribute_id = Column('id_attribute', Integer, ForeignKey('sp_attributes.id'), 
                          primary_key=True, nullable=False)
    access = Column(Unicode(15)) # denied, read-only, read/write
    
    ACCESS_DENIED = 'denied'
    ACCESS_READONLY = 'read-only'
    ACCESS_READWRITE = 'read/write'
    
    @staticmethod
    def get_privilege(id_user, id_attribute):
        
        priv = DBSession.query(SapnsAttrPrivilege).\
                filter(and_(SapnsAttrPrivilege.user_id == id_user,
                            SapnsAttrPrivilege.attribute_id == id_attribute
                            ))
                
        return priv
    
    @staticmethod
    def get_access(id_user, id_attribute):
    
        priv = SapnsAttrPrivilege.get_privilege(id_user, id_attribute)
        if priv is None:
            return SapnsAttrPrivilege.ACCESS_DENIED
        
        else:
            return priv.access
        
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
            
        DBSession.add(priv)
        DBSession.flush()
        
    @staticmethod
    def remove_privilege(id_user, id_attribute):
        DBSession.query(SapnsAttrPrivilege).\
            filter(and_(SapnsAttrPrivilege.user_id == id_user,
                        SapnsAttrPrivilege.attribute_id == id_attribute,
                        )).\
            delete()
            
        DBSession.flush()

class SapnsAction(DeclarativeBase):
    
    """
    List of available actions in Sapns
    """
    
    __tablename__ = 'sp_actions'
    
    action_id = Column('id', Integer, autoincrement=True, primary_key=True)

    name = Column(Unicode(100), nullable=False)
    url = Column(Unicode(200)) #, nullable=False)
    type = Column(Unicode(20), nullable=False)
    
    # TODO: puede ser nulo? (nullable=False)
    class_id = Column('id_class', Integer, ForeignKey('sp_classes.id'))
    
    TYPE_NEW = 'new'
    TYPE_EDIT = 'edit'
    TYPE_DELETE = 'delete'
    TYPE_REPORT = 'report'
    TYPE_PROCESS = 'process'
    TYPE_LIST = 'list'
    TYPE_OBJECT = 'object'
    TYPE_GROUP = 'group'
    
    # default URL
    URL_NEW = '/new'
    URL_EDIT = '/edit'
    URL_DELETE = '/delete'
    
class SapnsView(DeclarativeBase):
    
    """
    Views in Sapns
    """
    
    __tablename__ = 'sp_views'
    
    view_id = Column('id', Integer, autoincrement=True, primary_key=True)
    title = Column(Unicode(200), nullable=False)
    code = Column(Unicode(30), nullable=False)

class SapnsViewColumn(DeclarativeBase):
    
    """
    View columns in Sapns
    """
    
    __tablename__ = 'sp_view_columns'
    
    column_id = Column('id', Integer, autoincrement=True, primary_key=True)
    title = Column(Unicode(30), nullable=False)
    definition = Column(String, nullable=False)
    alias = Column(Unicode(100), nullable=False)
    order = Column(Integer)
    
    text_align = Column(Unicode(10))
    width = Column(Integer)
    
    view_id = Column('id_view', Integer, ForeignKey('sp_views.id'), nullable=False)
    # columns (SapnsViewColumn)
    # relations (SapnsViewRelation)
    # filters (SapnsViewFilter)
    # orders (SapnsViewOrder)
    
SapnsView.columns = \
    relation(SapnsViewColumn, 
             backref='view', 
             primaryjoin=SapnsView.view_id == SapnsViewColumn.view_id)
    
class SapnsViewRelation(DeclarativeBase):
    
    """
    View joins in Sapns
    """
    
    __tablename__ = 'sp_view_relations'
    
    relation_id = Column('id', Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(30), nullable=False)
    alias = Column(Unicode(100), nullable=False)
    condition = Column(String)
    
    view_id = Column('id_view', Integer, ForeignKey('sp_views.id'), nullable=False)
    
SapnsView.relations = \
    relation(SapnsViewRelation, 
             backref='view', 
             primaryjoin=SapnsView.view_id == SapnsViewRelation.view_id)
    
class SapnsViewFilter(DeclarativeBase):
    
    """
    'Where' clauses in Sapns views
    """
    
    __tablename__ = 'sp_view_filters'

    filter_id = Column('id', Integer, autoincrement=True, primary_key=True)
    
    definition = Column(String)
    active = Column(Boolean)

    view_id = Column('id_view', Integer, ForeignKey('sp_views.id'), nullable=False)
    
SapnsView.filters = \
    relation(SapnsViewFilter, 
             backref='view', 
             primaryjoin=SapnsView.view_id == SapnsViewFilter.view_id)

class SapnsViewOrder(DeclarativeBase):
    
    """
    Sort order in Sapns views
    """
    
    __tablename__ = 'sp_view_order'
    
    order_id = Column('id', Integer, autoincrement=True, primary_key=True)
    definition = Column(String)
    sort_order = Column(Integer)

    view_id = Column('id_view', Integer, ForeignKey('sp_views.id'), nullable=False)
    
SapnsView.orders = \
    relation(SapnsViewOrder, 
             backref='view', 
             primaryjoin=SapnsView.view_id == SapnsViewOrder.view_id)
    
class SapnsReport(DeclarativeBase):
    
    """
    Sapns reports (probably in JasperReports, for starters
    """
    
    __tablename__ = 'sp_reports'
    
    report_id = Column('id', Integer, autoincrement=True, primary_key=True)
    
    code = Column(Unicode(50), nullable=False, unique=True)
    name = Column(Unicode(200), nullable=False, unique=True)
    
    description = Column(String)

class SapnsReportParam(DeclarativeBase):
    
    """
    Sapns param list: so we know what to request from the user when we launch the report
    """
    
    __tablename__ = 'sp_report_parameters' 
    
    reportparam_id = Column('id', Integer, autoincrement=True, primary_key=True)
    
    name = Column(Unicode(200), nullable=False)
    
    class_id = Column('id_class', Integer, ForeignKey('sp_classes.id'), nullable=False)
    
    default_value = Column(Unicode(200))
    
    sort_order = Column(Integer)
    expression = Column(String)
    
    report_id = Column('id_report', Integer, ForeignKey('sp_reports.id'), nullable=False)
    
SapnsReport.params = \
    relation(SapnsReportParam, 
             backref='report', 
             primaryjoin=SapnsReport.report_id == SapnsReportParam.report_id)