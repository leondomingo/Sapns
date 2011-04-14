# -*- coding: utf-8 -*-
"""
  Modelo de datos básico de sapns 
"""
import os
import sys
from datetime import datetime

from sqlalchemy import ForeignKey, Column #, Table
from sqlalchemy.types import Unicode, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relation, synonym

from sapns.model import DeclarativeBase, metadata, DBSession
from sapns.model.auth import User
from sqlalchemy.sql.expression import and_

__all__ = ['SapnsShortcuts', 'SapnsClass', 'SapnsAttribute', 'SapnsAction',
           'SapnsView', 'SapnsViewAttribute', 'SapnsViewRelation',
           'SapnsViewFilter', 'SapnsViewOrder', 'SapnsReport',
           'SapnsReportParam',
           ]

class SapnsUsers(User):
    
    def shortcuts(self):
        sc = []
        for sc in DBSession.query(SapnsShortcuts).\
                filter(and_(SapnsShortcuts.user == self.user_id,
                            SapnsShortcuts.parent_id == None)).\
                order_by(SapnsShortcuts.order).\
                all():
            
            pass
        
        return sc

class SapnsShortcuts(DeclarativeBase):
    """
    Shortcuts sapns base table
    """

    __tablename__ = 'sp_shortcuts'

    shortcut_id = Column('id', Integer, autoincrement=True, primary_key=True)
    
    title = Column(Unicode(50))
    order = Column(Integer)
    parent_id = Column('id_parent_shortcut', Integer, ForeignKey('sp_shortcuts.id'))
    
    user = Column('id_user', Integer, ForeignKey('sp_users.id'), nullable=False)
    action = Column('id_action', Integer, ForeignKey('sp_actions.id'), nullable=False)
    
    def __repr__(self):
        return ('<Shortcut: user=%s, action=%s>' % self.user, self.action).encode('utf-8')

    def __unicode__(self):
        return u'<Shortcut: user=%s, action=%s>' % (self.user, self.action)
    

# TODO: 1-to-1 relation
SapnsShortcuts.children = \
    relation(SapnsShortcuts,
             backref='parent',
             primarykey=SapnsShortcuts.shortcut_id == SapnsShortcuts.parent_id)

class SapnsClass(DeclarativeBase):
    """
    List of sapns tables
    """

    __tablename__ = 'sp_classes'
    
    class_id = Column('id', Integer, autoincrement=True, primary_key=True )
    
    name = Column(Unicode(30), nullable=False)
    title = Column(Unicode(100), nullable=False)
    description = Column(String)
    
class SapnsAttribute(DeclarativeBase):
    
    """
    List of sapns columns in tables
    """
    
    __tablename__ = 'sp_attributes'

    attribute_id = Column('id', Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(30), nullable=False)
    title = Column(Unicode(100), nullable=False)
    
    class_id = Column('id_class', Integer, ForeignKey('sp_classes.id'), nullable=False)
    
    reference_order = Column(Integer)
    insertion_order = Column(Integer)
    
SapnsClass.attributes = \
    relation(SapnsAttribute,
             backref='class_',
             primaryjoin=SapnsClass.class_id == SapnsAttribute.class_id)

class SapnsPrivilege(DeclarativeBase):
    
    __tablename__ = 'sp_privilege'
    
    user_id = Column('id_user', Integer, ForeignKey('sp_users.id'), primary_key=True)
    class_id = Column('id_class', Integer, ForeignKey('sp_classes.id'), primary_key=True)
    
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
    
    user_id = Column('id_user', Integer, ForeignKey('sp_users.id'), primary_key=True)
    attribute_id = Column('id_attribute', Integer, ForeignKey('sp_attributes.id'), primary_key=True)
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
    url = Column(Unicode(200), nullable=False)
    type = Column(Unicode(80), nullable=False)
    
class SapnsView(DeclarativeBase):
    
    """
    Views in Sapns
    """
    
    __tablename__ = 'sp_views'
    
    view_id = Column('id', Integer, autoincrement=True, primary_key=True)
    
    title = Column(Unicode(200), nullable=False)

class SapnsViewAttribute(DeclarativeBase):
    
    """
    View columns in Sapns
    """
    
    __tablename__ = 'sp_view_attrs'
    
    viewattribute_id = Column('id', Integer, autoincrement=True, primary_key=True)
    
    title = Column(Unicode(30), nullable=False)
    definition = Column(String, nullable=False)
    alias = Column(Unicode(100), nullable=False)
    
    order = Column(Integer)
    
    text_align = Column(Unicode(10))
    width = Column(Integer)
    
    view = Column('id_view', Integer, ForeignKey('sp_views.id'), nullable=False)
    
class SapnsViewRelation(DeclarativeBase):
    
    """
    View joins in Sapns
    """
    
    __tablename__ = 'sp_view_relations'
    
    relation_id = Column('id', Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(30), nullable=False)
    alias = Column(Unicode(100), nullable=False)
    condition = Column(String)
    
    view = Column('id_view', Integer, ForeignKey('sp_views.id'), nullable=False)
    
class SapnsViewFilter(DeclarativeBase):
    
    """
    'Where' clauses in Sapns views
    """
    
    __tablename__ = 'sp_view_filters'

    filter_id = Column('id', Integer, autoincrement=True, primary_key=True)
    
    definition = Column(String)
    active = Column(Boolean)

    view = Column('id_view', Integer, ForeignKey('sp_views.id'), nullable=False)

class SapnsViewOrder(DeclarativeBase):
    
    """
    Sort order in Sapns views
    """
    
    __tablename__ = 'sp_view_order'
    
    order_id = Column('id', Integer, autoincrement=True, primary_key=True)
    definition = Column(String)
    sort_order = Column(Integer)

    view = Column('id_view', Integer, ForeignKey('sp_views.id'), nullable=False)
    
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
    
    sapnsclass = Column('id_class', Integer, ForeignKey('sp_classes.id'), nullable=False)
    
    default_value = Column(Unicode(200))
    
    sort_order = Column(Integer)
    expression = Column(String)
    
    report = Column('id_report', Integer, ForeignKey('sp_reports.id'), nullable=False)