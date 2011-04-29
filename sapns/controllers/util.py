# -*- coding: utf-8 -*-
"""Utilities controller"""

# turbogears imports
from tg import expose, url, response, config
from tg.i18n import set_lang

# third party imports
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from repoze.what import authorize

# project specific imports
from sapns.lib.base import BaseController
from sapns.model import DBSession

import logging
from sqlalchemy.schema import MetaData
from sqlalchemy.sql.expression import and_
from sqlalchemy.types import INTEGER, NUMERIC, BIGINT, DATE, TEXT, VARCHAR,\
    BOOLEAN, BLOB
from sqlalchemy.dialects.postgresql.base import TIME, TIMESTAMP, BYTEA
from pylons.templating import render_jinja2
from sapns.model.sapnsmodel import SapnsClass, SapnsAttribute, SapnsUser,\
    SapnsShortcut, SapnsAction, SapnsPrivilege, SapnsAttrPrivilege

class UtilController(BaseController):
    
    allow_only = authorize.has_any_permission('manage', 'utilities')
    
    @expose('message.html')
    def init(self):
        set_lang('en')
        self.update_metadata()
        self.create_dashboards()
        
        return dict(message=_('Initialization was completed successfully'),
                    came_from=url('/'))
    
    @expose('util/index.html')
    def index(self, came_from='/'):
        return dict(page='util', came_from=came_from)
    
    @expose('message.html')
    def create_dashboards(self, came_from='/util'):
        
        logger = logging.getLogger(__name__ + '/create_dashboards')
        
        for us in DBSession.query(SapnsUser):
            
            logger.info('Creating dashboard for "%s"' % us.display_name)
            
            # user's dashboard
            dboard = us.get_dashboard()
            if not dboard:
                
                dboard = SapnsShortcut()
                dboard.user_id = us.user_id
                dboard.parent_id = None
                dboard.title = unicode(l_('Dashboard'))
                dboard.order = 0
                
                DBSession.add(dboard)
                DBSession.flush()
                
                # data exploration
                
                data_ex = SapnsShortcut()
                data_ex.title = unicode(l_('Data exploration'))
                data_ex.parent_id = dboard.shortcut_id
                data_ex.user_id = us.user_id
                data_ex.order = 0
                
                DBSession.add(data_ex)
                DBSession.flush()
                
                # Data exploration/Sapns
                sc_sapns = SapnsShortcut()
                sc_sapns.title = 'Sapns'
                sc_sapns.parent_id = data_ex.shortcut_id
                sc_sapns.user_id = us.user_id
                sc_sapns.order = 0
                
                DBSession.add(sc_sapns)
                
                # Data exploration/Project
                sc_project = SapnsShortcut()
                sc_project.title = config.get('app.name', unicode(l_('Project')))
                sc_project.parent_id = data_ex.shortcut_id
                sc_project.user_id = us.user_id
                sc_project.order = 1
                
                DBSession.add(sc_project)
                DBSession.flush()
                
            else:
                logger.info('Dashboard already exists')
                data_ex = us.get_dataexploration()
                sc_sapns = data_ex.by_order(0)
                sc_project = data_ex.by_order(1)
                
            # data exploration/project
            tables = self.extract_model(all=True)['tables']
            
            for i, tbl in enumerate(tables):
                
                cls = DBSession.query(SapnsClass).\
                        filter(SapnsClass.name == tbl['name']).\
                        first()
                
                # look for this table action
                act_table = DBSession.query(SapnsAction).\
                                filter(and_(SapnsAction.type == SapnsAction.TYPE_LIST,
                                            SapnsAction.class_id == cls.class_id)).\
                                first()
                                
                if not act_table:
                    act_table = SapnsAction()
                    act_table.name = unicode(l_('List'))
                    act_table.type = SapnsAction.TYPE_LIST
                    act_table.class_id = cls.class_id
                    
                    DBSession.add(act_table)
                    DBSession.flush()
                    
                # project
                sc_parent = sc_project.shortcut_id
                if cls.name.startswith('sp_'):
                    # sapns
                    sc_parent = sc_sapns.shortcut_id
                    
                sc_table = DBSession.query(SapnsShortcut).\
                        filter(and_(SapnsShortcut.parent_id == sc_parent,
                                    SapnsShortcut.action_id == act_table.action_id,
                                    SapnsShortcut.user_id == us.user_id,
                                    )).\
                        first()
                        
                # does this user have this class shortcut?
                if not sc_table:
                    sc_table = SapnsShortcut()
                    sc_table.title = tbl['name']
                    sc_table.parent_id = sc_parent
                    sc_table.user_id = us.user_id
                    sc_table.action_id = act_table.action_id
                    sc_table.order = i
    
                    DBSession.add(sc_table)
                    DBSession.flush()
                
                    # privileges
                    priv = SapnsPrivilege()
                    priv.user_id = us.user_id
                    priv.class_id = cls.class_id
                
                    DBSession.add(priv)
                    DBSession.flush()
                    
                else:
                    logger.info('Shortcut for "%s" already exists' % cls.title)
                
                # attribute privileges
                for attr in DBSession.query(SapnsAttribute).\
                        filter(SapnsAttribute.class_id == cls.class_id).\
                        all():
                    
                    #if not SapnsAttrPrivilege.get_privilege(us.user_id, attr.attribute_id):
                    if not us.attr_privilege(attr.attribute_id):
                        priv_attr = SapnsAttrPrivilege()
                        priv_attr.user_id = us.user_id
                        priv_attr.attribute_id = attr.attribute_id
                        priv_attr.access = SapnsAttrPrivilege.ACCESS_READWRITE
                        
                        DBSession.add(priv_attr)
                        DBSession.flush()
                        
                    else:
                        logger.info('Privilege for "%s" already exists' % attr.title)

        return dict(message=_('The user dashboards have been created'), 
                    came_from=url(came_from))
    
    @expose('message.html')
    def update_metadata(self, came_from='/util'):
        
        logger = logging.getLogger(__name__ + '/update_metadata')
        
        tables = self.extract_model(all=True)['tables']
        tables_id = {}
        pending_attr = {}
        for tbl in tables:
            
            logger.info('Table: %s' % tbl['name'])
            
            klass = DBSession.query(SapnsClass).\
                        filter(SapnsClass.name == tbl['name']).\
                        first()
            
            if not klass:
                logger.warning('.....creating')
                
                klass = SapnsClass()
                klass.name = tbl['name']
                klass.title = tbl['name'].title()
                desc = unicode(l_('Class: %s'))
                klass.description =  desc % tbl['name']
                
                DBSession.add(klass)
                DBSession.flush()
                
            else:
                logger.warning('.....already exists')
                
            tables_id[tbl['name']] = klass.class_id
                
            # create an action
            def create_action(name, type_):
                action = DBSession.query(SapnsAction).\
                            filter(and_(SapnsAction.class_id == klass.class_id,
                                        SapnsAction.type == type_)).\
                            first()
                                
                if not action:
                    action = SapnsAction()
                    action.name = name
                    action.type = type_
                    action.class_id = klass.class_id
                    
                    DBSession.add(action)
                    DBSession.flush()
                    
            # create standard actions
            create_action(unicode(l_('New')), SapnsAction.TYPE_NEW)
            create_action(unicode(l_('Edit')), SapnsAction.TYPE_EDIT)
            create_action(unicode(l_('Delete')), SapnsAction.TYPE_DELETE)
            create_action(unicode(l_('List')), SapnsAction.TYPE_LIST)
                
            first_ref = False
            for i, col in enumerate(tbl['columns']):
                
                logger.info('Column: %s' % col['name'])
                
                attr = DBSession.query(SapnsAttribute).\
                        filter(and_(SapnsAttribute.name == col['name'],
                                    SapnsAttribute.class_id == klass.class_id, 
                                    )).\
                        first()
                        
                if not attr and col['name'] != 'id':
                    logger.warning('.....creating')
                    
                    attr = SapnsAttribute()
                    attr.name = col['name']
                    attr.title = col['name'].replace('_', ' ').title()
                    attr.class_id = klass.class_id
                    attr.type = col['type_name']
                    if attr.type == 'Unicode' and not first_ref:
                        attr.reference_order = 0
                        first_ref = True
                        
                    attr.visible = True
                        
                    attr.insertion_order = i
                    attr.is_collection = False
                    
                    DBSession.add(attr)
                    DBSession.flush()
                    
                else:
                    logger.warning('.....already exists')
                    
                # foreign key
                if col['fk_table'] != None:
                    pending_attr[attr.attribute_id] = col['fk_table'].name
            
        # update related classes
        for attr_id, fk_table in pending_attr.iteritems():
            attr = DBSession.query(SapnsAttribute).get(attr_id)
            attr.related_class_id = tables_id[fk_table]
            
            DBSession.add(attr)
            DBSession.flush()

        return dict(message=_('Process terminated'), came_from=url(came_from))
    
    @expose(content_type='text/plain')
    def code_model(self, app_name='MyApp', file_name=''):
        mdl = self.extract_model()
        if file_name:
            response.headerlist.append(('Content-Disposition', 
                                        'attachment;filename=%s' % file_name))

        return render_jinja2('util/model.template',
                             extra_vars=dict(app_name=app_name,
                                             tables=mdl['tables']))
    
    @expose('util/tables.html')
    def extract_model(self, all=False):
        
        logger = logging.getLogger(__name__ + '/extract_model')
        
        meta = MetaData(bind=DBSession.bind, reflect=True)
        logger.info('Connected to "%s"' % meta.bind)
        
        def sp_cmp(x, y):
            """Alphabetical order but sp_* tables before any other table."""
            
            if x.name.startswith('sp_'):
                if y.name.startswith('sp_'):
                    return cmp(x.name, y.name)
                
                else:
                    return -1
                
            else:
                if y.name.startswith('sp_'):
                    return 1
                
                else:
                    return cmp(x.name, y.name)
        
        tables = []
        for tbl in sorted(meta.sorted_tables, cmp=sp_cmp):
            
            if not tbl.name.startswith('sp_') or all:
                
                logger.info('Table: %s' % tbl.name)
                
                t = dict(name=tbl.name,
                         columns=[])
                
                # class name
                class_name = [i.title() for i in tbl.name.split('_')]
                t['class_name'] = ''.join(class_name)
                
                t['pk'] = [k for k in tbl.primary_key.columns.keys()]
                
                fk_cols = []
                fk_tables = []
                for fk in tbl.foreign_keys:
                    logger.info(fk.parent)
                    fk_tables.append(fk.column.table)
                    fk_cols.append(fk.parent.name)
                    
                for c in tbl.columns:
                    col = dict(name=c.name, type=repr(c.type), fk='-', 
                               length=None, prec=None, scale=None,
                               pk=False)

                    # is primary key?                    
                    col['pk'] = c.name in tbl.primary_key.columns.keys()
                    
                    logger.info('%s' % type(c.type))
                    
                    type_name = '---'
                    if isinstance(c.type, INTEGER):
                        type_name = 'Integer'
                        
                    elif isinstance(c.type, NUMERIC):
                        type_name = 'Numeric'
                        col['prec'] = c.type.precision
                        col['scale'] = c.type.scale
                        
                    elif isinstance(c.type, BIGINT):
                        type_name = 'Integer'

                    elif isinstance(c.type, DATE):
                        type_name = 'Date'
                        
                    elif isinstance(c.type, TIME):
                        type_name = 'Time'
                        
                    elif isinstance(c.type, TIMESTAMP):
                        type_name = 'DateTime'

                    elif isinstance(c.type, VARCHAR):
                        type_name = 'Unicode'
                        col['length'] = c.type.length
                        
                    elif isinstance(c.type, TEXT):
                        type_name = 'String'
                        
                    elif isinstance(c.type, BOOLEAN):
                        type_name = 'Boolean'
                        
                    elif isinstance(c.type, BLOB):
                        type_name = 'blob'
                        
                    elif isinstance(c.type, BYTEA):
                        type_name = 'bytea'
                        
                    else:
                        type_name = '(%s)' % str(c.type)
                        
                    col['type_name'] = type_name
                    
                    try:
                        i = fk_cols.index(c.name)
                        col['fk_table'] = fk_tables[i]
                        
                    except:
                        col['fk_table'] = None
                        
                    t['columns'].append(col)
                    
                tables.append(t)
                
        return dict(page='extract_model', came_from=url('/util'), 
                    tables=tables)