# -*- coding: utf-8 -*-
"""Views management controller"""

# turbogears imports
from tg import expose, url, response, redirect, config
from tg.i18n import set_lang

# third party imports
from pylons.i18n import ugettext as _
from repoze.what import authorize, predicates

# project specific imports
from sapns.lib.base import BaseController
from sapns.model import DBSession, metadata

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
    # only for "managers"
    allow_only = authorize.has_permission('manage')
    
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
        
        for us in DBSession.query(SapnsUser).all():
            
            logger.info('Creating dashboard for "%s"' % us.display_name)
            
            # user's dashboard
            dboard = us.get_dashboard()
            if not dboard:
                
                dboard = SapnsShortcut()
                dboard.user_id = us.user_id
                dboard.parent_id = None
                dboard.title = _('Dashboard')
                dboard.order = 0
                
                DBSession.add(dboard)
                DBSession.flush()
                
                # data exploration
                
                data_ex = SapnsShortcut()
                data_ex.title = _('Data exploration')
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
                sc_project.title = config.get('app.name', _('Project'))
                sc_project.parent_id = data_ex.shortcut_id
                sc_project.user_id = us.user_id
                sc_project.order = 1
                
                DBSession.add(sc_project)
                DBSession.flush()
                
                # data exploration/project
                tables = self.extract_model()['tables']
                
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
                        act_table.name = _('List')
                        act_table.type = SapnsAction.TYPE_LIST
                        act_table.class_id = cls.class_id
                        
                        DBSession.add(act_table)
                        DBSession.flush()
                    
                    sc_table = SapnsShortcut()
                    sc_table.title = tbl['name']
                    sc_table.parent_id = sc_project.shortcut_id
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
                    
                    # attribute privileges
                    for atr in DBSession.query(SapnsAttribute).\
                            filter(SapnsAttribute.class_id == cls.class_id).\
                            all():
                        
                        priv_atr = SapnsAttrPrivilege()
                        priv_atr.user_id = us.user_id
                        priv_atr.attribute_id = atr.attribute_id
                        priv_atr.access = SapnsAttrPrivilege.ACCESS_READWRITE
                        
                        DBSession.add(priv_atr)
                        DBSession.flush()

        return dict(message=_('The user dashboards have been created'), 
                    came_from=url(came_from))
    
    @expose('message.html')
    def update_metadata(self, came_from='/util'):
        
        logger = logging.getLogger(__name__ + '/update_metadata')
        
        tables = self.extract_model()['tables']
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
                desc = _('Class: %s')
                klass.description =  desc % tbl['name']
                
                DBSession.add(klass)
                DBSession.flush()
                
            else:
                logger.warning('.....already exists')
                
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
            create_action(_('New'), SapnsAction.TYPE_NEW)
            create_action(_('Edit'), SapnsAction.TYPE_EDIT)
            create_action(_('Delete'), SapnsAction.TYPE_DELETE)
            create_action(_('List'), SapnsAction.TYPE_LIST)
                
            for i, col in enumerate(tbl['columns']):
                
                logger.info('Column: %s' % col['name'])
                
                atr = DBSession.query(SapnsAttribute).\
                        filter(and_(SapnsAttribute.name == col['name'],
                                    SapnsAttribute.class_id == klass.class_id, 
                                    )).\
                        first()
                        
                if not atr and col['name'] != 'id':
                    logger.warning('.....creating')
                    
                    atr = SapnsAttribute()
                    atr.name = col['name']
                    atr.title = col['name'].replace('_', ' ').title()
                    atr.class_id = klass.class_id
                    atr.type_ = col['type_name']
                    atr.reference_order = i
                    atr.insertion_order = i
                    atr.is_collection = False
                    
                    DBSession.add(atr)
                    DBSession.flush()
                    
                else:
                    logger.warning('.....already exists')
                    
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
        
        tables = []
        for tbl in sorted(meta.sorted_tables, 
                          # table name alphabetical order
                          cmp=lambda x,y: cmp(x.name, y.name)):
            
            if not tbl.name.startswith('sp_') or all:
                
                logger.info('Table: %s' % tbl.name)
                
                t = dict(name=tbl.name,
                         columns=[])
                
                # class name
                class_name = [i.title() for i in tbl.name.split('_')]
                t['class_name'] = ''.join(class_name)
                
                #t['pk'] = dir(tbl.primary_key)
                t['pk'] = [k for k in tbl.primary_key.columns.keys()] #['id'].name
                
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