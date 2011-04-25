# -*- coding: utf-8 -*-
"""
  Modelo de datos básico de sapns 
"""
import os
import sys
from datetime import datetime

from pylons.i18n import ugettext as _

from tg import config

from sqlalchemy import MetaData, Table, ForeignKey, Column, UniqueConstraint, DefaultClause
from sqlalchemy.sql.expression import and_, select, alias
from sqlalchemy.types import Unicode, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relation, synonym

from sapns.model import DeclarativeBase, metadata, DBSession
from sapns.model.auth import User

import logging
from neptuno.util import datetostr

__all__ = ['SapnsAction', 'SapnsAttrPrivilege', 'SapnsAttribute',
           'SapnsClass', 'SapnsPrivilege', 'SapnsReport', 'SapnsReportParam',
           'SapnsShortcut', 'SapnsUser', 'SapnsView', 'SapnsViewColumn',
           'SapnsViewFilter', 'SapnsViewOrder', 'SapnsViewRelation',
          ]

# inherited class from "User"
class SapnsUser(User):
    
    def get_dashboard(self):
        dboard = DBSession.query(SapnsShortcut).\
                    filter(and_(SapnsShortcut.user_id == self.user_id,
                                SapnsShortcut.parent_id == None)).\
                    first()
                    
        return dboard
    
    def get_dataexploration(self):
        data_exploration = DBSession.query(SapnsShortcut).\
                filter(and_(SapnsShortcut.parent_id == self.get_dashboard().shortcut_id,
                            SapnsShortcut.order == 0,
                            )).\
                first()
                
        return data_exploration
    
    def get_shortcuts(self, id_parent=None):
        
        #logger = logging.getLogger('SapnsUser.get_shortcuts')

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
            
            #logger.info('Getting shortcut "%s"' % sc.title)
            url = ''
            type_ = ''
            class_ = ''
            if ac:
                url = ac.url
                type_ = ac.type
                
                if cl:
                    class_ = cl.name 
                            
            shortcuts.append(dict(url=url, 
                                  title=_(sc.title),
                                  action_type=type_,
                                  cls=class_,
                                  parent=sc.parent_id, 
                                  id=sc.shortcut_id))
        
        return shortcuts
    
    def copy_from(self, other_id):
        
        logger = logging.getLogger('SapnsUser.copy_from')
        try:
            # shortcuts
            logger.info('Copying shortcuts')
            parents = {}
            for sc in DBSession.query(SapnsShortcut).\
                    filter(SapnsShortcut.user_id == other_id):
                
                sc_copy = SapnsShortcut()
                sc_copy.title = sc.title
                sc_copy.parent_id = sc.parent_id
                sc_copy.user_id = self.user_id
                sc_copy.action_id = sc.action_id
                sc_copy.order = sc.order
                
                DBSession.add(sc_copy)
                DBSession.flush()
                
                parents[sc.shortcut_id] = sc_copy.shortcut_id
                
            logger.info('Updating parents')
            for sc_copy in DBSession.query(SapnsShortcut).\
                    filter(and_(SapnsShortcut.user_id == self.user_id,
                                SapnsShortcut.parent_id != None)):

                # update parent shortcut
                sc_copy.parent_id = parents[sc_copy.parent_id]
                DBSession.add(sc_copy)
                DBSession.flush()
                
            # privileges (on classes)
            logger.info('Copying privileges')
            for priv in DBSession.query(SapnsPrivilege).\
                    filter(SapnsPrivilege.user_id == other_id):

                priv_copy = SapnsPrivilege()
                priv_copy.class_id = priv.class_id
                priv_copy.user_id = self.user_id
                
                DBSession.add(priv_copy)
                DBSession.flush()
            
            # attribute privileges
            logger.info('Copying attribute privileges')
            for ap in DBSession.query(SapnsAttrPrivilege).\
                    filter(SapnsAttrPrivilege.user_id == other_id):
                
                ap_copy = SapnsAttrPrivilege()
                ap_copy.user_id = self.user_id
                ap_copy.attribute_id = ap.attribute_id
                ap_copy.access = ap.access
                
                DBSession.add(ap_copy)
                DBSession.flush()
                
        except Exception, e:
            logger.error(e)
    
    def has_privilege(self, cls):
        priv = DBSession.query(SapnsPrivilege).\
                join((SapnsClass, 
                      SapnsClass.class_id == SapnsPrivilege.class_id)).\
                filter(and_(SapnsPrivilege.user_id == self.user_id, 
                            SapnsClass.name == cls)).\
                first()
                
        return priv != None
    
    def attr_privilege(self, id_attribute):
        priv_atr = DBSession.query(SapnsAttrPrivilege).\
                filter(and_(SapnsAttrPrivilege.user_id == self.user_id,
                            SapnsAttrPrivilege.attribute_id == id_attribute,
                            )).\
                first()
                
        return priv_atr

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
    
    def __repr__(self):
        return ('<Shortcut: user=%s, action=%s>' % self.user, self.action).encode('utf-8')

    def __unicode__(self):
        return u'<Shortcut: user=%s, action=%s>' % (self.user, self.action)
    
    def by_order(self, order):
        """Return a 'child' shortcut (of this) with the indicated 'order'"""
        sc = DBSession.query(SapnsShortcut).\
                filter(and_(SapnsShortcut.parent_id == self.shortcut_id,
                            SapnsShortcut.order == order)).\
                first()
                
        return sc

# TODO: 1-to-1 autoreference relation
SapnsShortcut.children = \
    relation(SapnsShortcut,
             backref='parent',
             uselist=False,
             remote_side=[SapnsShortcut.shortcut_id],
             primaryjoin=SapnsShortcut.shortcut_id == SapnsShortcut.parent_id)

class SapnsClass(DeclarativeBase):
    """List of sapns tables"""

    __tablename__ = 'sp_classes'
    __table_args__ = (UniqueConstraint('name'), {})
    
    class_id = Column('id', Integer, autoincrement=True, primary_key=True)
    
    name = Column(Unicode(50), nullable=False)
    title = Column(Unicode(100), nullable=False)
    description = Column(String)
    
    # attributes (SapnsAttribute)
    
    @staticmethod
    def by_name(class_name):
        """
        Returns the SapnsClass whose name is "class_name"
        IN
          class_name  <unicode>
          
        OUT
          <SapnsClass>
        """
        cls = DBSession.query(SapnsClass).\
            filter(SapnsClass.name == class_name).\
            first()
            
        return cls
    
    @staticmethod
    def class_titles(class_name):
        
        logger = logging.getLogger(__name__ + '/class_titles')
        
        date_fmt = config.get('grid.date_format', default='%m/%d/%Y')
        
        def __class_title(class_name, qry=None, attr=None):
            
            try:
                meta = MetaData(bind=DBSession.bind)
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
                        rel_class = DBSession.query(SapnsClass).get(r['related_class_id'])
                        names_rel, types_rel, qry = __class_title(rel_class.name, 
                                                       qry=qry, attr=tbl.c[r['name']])
                        names += names_rel
                        types += types_rel
                        
                return names, types, qry
            
            except Exception, e:
                logger.error(e)
                
        names, types, qry = __class_title(class_name, qry=None)
        
        sel = select(names, from_obj=qry, use_labels=True)
        logger.info(sel)
        
        MAX_VALUES = 5000
        titles = []
        for row in DBSession.execute(sel.limit(MAX_VALUES)):
            
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
    
    @staticmethod
    def object_title(class_name, id_object):
        
        logger = logging.getLogger(__name__ + '/object_title')
        
        if id_object is None:
            return ''
        
        date_fmt = config.get('grid.date_format', default='%m/%d/%Y')
        
        meta = MetaData(bind=DBSession.bind)
        cls = SapnsClass.by_name(class_name)
        tbl = Table(cls.name, meta, autoload=True)
        row = DBSession.execute(tbl.select(whereclause=tbl.c.id == id_object)).fetchone()
        ref = []
        for r in cls.reference():
            
            logger.info(r['name'])
            
            if not r['related_class_id']:
                
                value = row[r['name']]
                if value:
                    if r['type'] == SapnsAttribute.TYPE_DATE:
                        value = datetostr(value, fmt=date_fmt)
                        
                    else:
                        value = unicode(value)
                else:
                    value = '' 
                
                ref.append(value)
                
            else:
                # related attribute
                rel_class = DBSession.query(SapnsClass).get(r['related_class_id'])
                rel_ref = SapnsClass.object_title(rel_class.name, row[r['name']])
                
                ref.append(rel_ref)
                
        return '.'.join(ref)

    def sorted_actions(self):
        """
        Returns a list of actions associated with this class.
        
        OUT
          [{"title": <unicode>, "url": <unicode>, "require_id": <bool>}, ...]
        """
        
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
    
    def insertion(self):
        """
        Return the list of attributes in "order of insertion" for this class.
        
        OUT
          [{"id": <int>, "title": <unicode>, "name": <unicode>,
            "required": <bool>, "visible": <bool>}, ...]
        """
        
        ins = []
        for attr in DBSession.query(SapnsAttribute).\
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
        for attr in DBSession.query(SapnsAttribute).\
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
        
        attr = DBSession.query(SapnsAttribute).\
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
          [{"id": <int>, 
            "name": <unicode>, 
            "title": <unicode>,
            "attr_id": <int>, 
            "attr_name": <unicode>,
            "attr_title": <unicode>}, ...]
        """
        
        related_classes = []
        for cls, attr in DBSession.query(SapnsClass, SapnsAttribute).\
                join((SapnsAttribute, 
                      SapnsAttribute.class_id == SapnsClass.class_id)).\
                filter(SapnsAttribute.related_class_id == self.class_id):
            
            rc = dict(id=cls.class_id, name=cls.name, title=cls.title,
                      attr_id=attr.attribute_id,
                      attr_name=attr.name, attr_title=attr.title)
            
            related_classes.append(rc)
            
        return related_classes
                
                
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
    
    TYPE_INTEGER = 'Integer'
    TYPE_BOOLEAN = 'Boolean'
    TYPE_NUMERIC = 'Numeric'
    TYPE_UNICODE = 'Unicode'
    TYPE_STRING = 'String' # memo type
    TYPE_DATE = 'Date'
    TYPE_TIME = 'Time'
    TYPE_DATETIME = 'DateTime'
    
    type = Column(Unicode(20), nullable=False)
    required = Column(Boolean, DefaultClause('false'), default=False)
    reference_order = Column(Integer)
    insertion_order = Column(Integer)
    visible = Column(Boolean, DefaultClause('true'), default=True)
    is_collection = Column(Boolean, DefaultClause('false'), default=False)
    
SapnsClass.attributes = \
    relation(SapnsAttribute,
             backref='class_',
             primaryjoin=SapnsClass.class_id == SapnsAttribute.class_id)

class SapnsPrivilege(DeclarativeBase):
    
    __tablename__ = 'sp_privilege'
    
    user_id = Column('id_user', Integer, 
                     ForeignKey('sp_users.id', 
                                onupdate='CASCADE', ondelete='CASCADE'), 
                     primary_key=True, nullable=False)
    
    class_id = Column('id_class', Integer, 
                      ForeignKey('sp_classes.id', onupdate='CASCADE', ondelete='CASCADE'), 
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
    
    user_id = Column('id_user', Integer, 
                     ForeignKey('sp_users.id', 
                                onupdate='CASCADE', ondelete='CASCADE'), 
                     primary_key=True, nullable=False)
    
    attribute_id = Column('id_attribute', Integer, 
                          ForeignKey('sp_attributes.id',
                                     onupdate='CASCADE', ondelete='CASCADE'), 
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
    
    """View columns in Sapns"""
    
    __tablename__ = 'sp_view_columns'
    
    column_id = Column('id', Integer, autoincrement=True, primary_key=True)
    title = Column(Unicode(30), nullable=False)
    definition = Column(String, nullable=False)
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
    condition = Column(String)
    
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
    
    definition = Column(String)
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
    definition = Column(String)
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
    
    description = Column(String)

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
    expression = Column(String)
    
    report_id = Column('id_report', Integer, 
                       ForeignKey('sp_reports.id',
                                  onupdate='CASCADE', ondelete='CASCADE'), 
                       nullable=False)
    
SapnsReport.params = \
    relation(SapnsReportParam, 
             backref='report', 
             primaryjoin=SapnsReport.report_id == SapnsReportParam.report_id)