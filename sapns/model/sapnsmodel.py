# -*- coding: utf-8 -*-
"""
  Modelo de datos básico de sapns 
"""
import os
from datetime import datetime
import sys

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime, String, Boolean
from sqlalchemy.orm import relation, synonym

from sapns.model import DeclarativeBase, metadata, DBSession

__all__ = ['SapnsShortcuts', 'SapnsClass', 'SapnsAttribute', 'SapnsAction',
           'SapnsView', 'SapnsViewAttribute', 'SapnsViewRelation',
           'SapnsViewFilter', 'SapnsViewOrder', 'SapnsReport',
           'SapnsReportParam',
           ]

class SapnsShortcuts(DeclarativeBase):
    """
    Shortcuts sapns base table
    """

    __tablename__ = 'sp_shortcuts'

    shortcut_id = Column('id', Integer, autoincrement=True, primary_key=True)
    
    title = Column(Unicode(50))
    order = Column(Integer)
    parent_id = Column(Integer)
    
    user = Column('id_user', Integer, ForeignKey('sp_users.id'), nullable=False)
    action = Column('id_action', Integer, ForeignKey('sp_actions.id'), nullable=False)
    
    def __repr__(self):
        return ('<Shortcut: user=%s, action=%s>' % self.user, self.action).encode('utf-8')

    def __unicode__(self):
        return u'<Shortcut: user=%s, action=%s>' % (self.user, self.action)


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
    
    sapnsclass = Column('id_class', Integer, ForeignKey('sp_classes.id'), nullable=False)
    
    reference_order = Column(Integer)
    insertion_order = Column(Integer)

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