# -*- coding: utf-8 -*-

from tg import config
from pylons.i18n import lazy_ugettext as l_

from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsClass, SapnsPermission, SapnsAttribute,\
    SapnsUser, SapnsShortcut, SapnsAttrPrivilege, SapnsRole, SapnsUserRole
    
import logging
from sqlalchemy import MetaData
from sqlalchemy.sql.expression import and_
from sqlalchemy.types import INTEGER, NUMERIC, BIGINT, DATE, TEXT, VARCHAR,\
    BOOLEAN, BLOB
from sqlalchemy.dialects.postgresql.base import TIME, TIMESTAMP, BYTEA
from pylons.templating import render_jinja2

ROLE_MANAGERS = u'managers'

def extract_model(all=False): 
    logger = logging.getLogger('lib.sapns.extract_model')
    
    meta = MetaData(bind=dbs.bind, reflect=True)
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
                    type_name = SapnsAttribute.TYPE_INTEGER
                    
                elif isinstance(c.type, NUMERIC):
                    type_name = SapnsAttribute.TYPE_FLOAT
                    col['prec'] = c.type.precision
                    col['scale'] = c.type.scale
                    
                elif isinstance(c.type, BIGINT):
                    type_name = SapnsAttribute.TYPE_INTEGER

                elif isinstance(c.type, DATE):
                    type_name = SapnsAttribute.TYPE_DATE
                    
                elif isinstance(c.type, TIME):
                    type_name = SapnsAttribute.TYPE_TIME
                    
                elif isinstance(c.type, TIMESTAMP):
                    type_name = SapnsAttribute.TYPE_DATETIME

                elif isinstance(c.type, VARCHAR):
                    type_name = SapnsAttribute.TYPE_STRING
                    col['length'] = c.type.length
                    
                elif isinstance(c.type, TEXT):
                    type_name = SapnsAttribute.TYPE_MEMO
                    
                elif isinstance(c.type, BOOLEAN):
                    type_name = SapnsAttribute.TYPE_BOOLEAN
                    
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
            
    return tables
        
def update_metadata():
    
    logger = logging.getLogger('lib.sapns.update_metadata')
    
    managers = SapnsRole.by_name(ROLE_MANAGERS)
    #managers = SapnsRole()
    
    tables = extract_model(all=True)
    tables_id = {}
    pending_attr = {}
    for tbl in tables:
        
        logger.info('Table: %s' % tbl['name'])
        
        klass = dbs.query(SapnsClass).\
                    filter(SapnsClass.name == tbl['name']).\
                    first()
        
        if not klass:
            logger.warning('.....creating')
            
            klass = SapnsClass()
            klass.name = tbl['name']
            klass.title = tbl['name'].title()
            desc = unicode(l_('Class: %s'))
            klass.description =  desc % tbl['name']
            
            dbs.add(klass)
            dbs.flush()
            
            # # grant access (r/w) to managers
            managers.add_privilege(klass.class_id)

        else:
            logger.warning('.....already exists')
            
        tables_id[tbl['name']] = klass.class_id
            
        # create an action
        def create_action(name, type_):
            action = dbs.query(SapnsPermission).\
                        filter(and_(SapnsPermission.class_id == klass.class_id,
                                    SapnsPermission.type == type_)).\
                        first()
                            
            if not action:
                action = SapnsPermission()
                action.permission_name = '%s#%s' % (klass.name, name.lower())
                action.display_name = name
                action.type = type_
                action.class_id = klass.class_id
                
                dbs.add(action)
                dbs.flush()
                
                # add this action to "managers" role
                managers.permissions_.append(action)
                dbs.flush()
                
        # create standard actions
        create_action(unicode(l_('New')), SapnsPermission.TYPE_NEW)
        create_action(unicode(l_('Edit')), SapnsPermission.TYPE_EDIT)
        create_action(unicode(l_('Delete')), SapnsPermission.TYPE_DELETE)
        create_action(unicode(l_('List')), SapnsPermission.TYPE_LIST)
        create_action(unicode(l_('Docs')), SapnsPermission.TYPE_DOCS)
            
        first_ref = False
        for i, col in enumerate(tbl['columns']):
            
            logger.info('Column: %s' % col['name'])
            
            attr = dbs.query(SapnsAttribute).\
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
                if attr.type == SapnsAttribute.TYPE_STRING and not first_ref:
                    attr.reference_order = 0
                    first_ref = True
                    
                attr.visible = True
                    
                attr.insertion_order = i
                attr.is_collection = False
                
                dbs.add(attr)
                dbs.flush()
                
                # grant access (r/w) to managers
                rw_access = SapnsAttrPrivilege.ACCESS_READWRITE
                managers.add_attr_privilege(attr.attribute_id, rw_access)
                
            else:
                logger.warning('.....already exists')
                
            # foreign key
            if col['fk_table'] != None:
                pending_attr[attr.attribute_id] = col['fk_table'].name
        
    # update related classes
    for attr_id, fk_table in pending_attr.iteritems():
        attr = dbs.query(SapnsAttribute).get(attr_id)
        attr.related_class_id = tables_id[fk_table]
        
        dbs.add(attr)
        dbs.flush()
    
    
def create_dashboards(us):
    
    logger = logging.getLogger('lib.sapns.util.create_dashboards')
    
    #us = dbs.query(SapnsUser).get(id_user)
        
    logger.info('Creating dashboard for "%s"' % us.display_name)
    
    # user's dashboard
    dboard = us.get_dashboard()
    if not dboard:
        
        dboard = SapnsShortcut()
        dboard.user_id = us.user_id
        dboard.parent_id = None
        dboard.title = unicode(l_('Dashboard'))
        dboard.order = 0
        
        dbs.add(dboard)
        dbs.flush()
        
        # data exploration
        
        data_ex = SapnsShortcut()
        data_ex.title = unicode(l_('Data exploration'))
        data_ex.parent_id = dboard.shortcut_id
        data_ex.user_id = us.user_id
        data_ex.order = 0
        
        dbs.add(data_ex)
        dbs.flush()
        
        # Data exploration/Sapns
        sc_sapns = SapnsShortcut()
        sc_sapns.title = 'Sapns'
        sc_sapns.parent_id = data_ex.shortcut_id
        sc_sapns.user_id = us.user_id
        sc_sapns.order = 0
        
        dbs.add(sc_sapns)
        
        # Data exploration/Project
        sc_project = SapnsShortcut()
        sc_project.title = config.get('app.name', unicode(l_('Project')))
        sc_project.parent_id = data_ex.shortcut_id
        sc_project.user_id = us.user_id
        sc_project.order = 1
        
        dbs.add(sc_project)
        dbs.flush()
        
    else:
        logger.info('Dashboard already exists')
        
def create_data_exploration():
    
    managers = SapnsRole.by_name(ROLE_MANAGERS)
    #managers = SapnsRole()
    
    logger = logging.getLogger('lib.sapns.util.create_data_exploration')
    
    tables = extract_model(all=True) #['tables']

    for us in dbs.query(SapnsUser).\
        join((SapnsUserRole,
              and_(SapnsUserRole.user_id == SapnsUser.user_id,
                   SapnsUserRole.role_id == managers.group_id,
                   ))):
        
        create_dashboards(us)
        
        data_ex = us.get_dataexploration()
        sc_sapns = data_ex.by_order(0)
        sc_project = data_ex.by_order(1)
        
        # data exploration/project       
        for i, tbl in enumerate(tables):
            
            cls = dbs.query(SapnsClass).\
                    filter(SapnsClass.name == tbl['name']).\
                    first()
            
            # look for this table "list" action
            act_table = dbs.query(SapnsPermission).\
                filter(and_(SapnsPermission.type == SapnsPermission.TYPE_LIST,
                            SapnsPermission.class_id == cls.class_id)).\
                first()
                            
            if not act_table:
                act_table = SapnsPermission()
                act_table.permission_name = '%s#%s' % (cls.name, SapnsPermission.TYPE_LIST)
                act_table.display_name = unicode(l_('List'))
                act_table.type = SapnsPermission.TYPE_LIST
                act_table.class_id = cls.class_id
                
                dbs.add(act_table)
                dbs.flush()
                
                # add to "managers" role
                managers.permissions_.append(act_table)
                dbs.flush()
                
            # project
            sc_parent = sc_project.shortcut_id
            if cls.name.startswith('sp_'):
                # sapns
                sc_parent = sc_sapns.shortcut_id
                
            sc_table = dbs.query(SapnsShortcut).\
                    filter(and_(SapnsShortcut.parent_id == sc_parent,
                                SapnsShortcut.permission_id == act_table.permission_id,
                                SapnsShortcut.user_id == us.user_id,
                                )).\
                    first()
                    
            # does this user have this class shortcut?
            if not sc_table:
                sc_table = SapnsShortcut()
                sc_table.title = tbl['name']
                sc_table.parent_id = sc_parent
                sc_table.user_id = us.user_id
                sc_table.permission_id = act_table.permission_id
                sc_table.order = i
    
                dbs.add(sc_table)
                dbs.flush()
            
            else:
                logger.info('Shortcut for "%s" already exists' % cls.title)

def topdf(html_content, **kw):
    
    import subprocess as sp
    import tempfile
    import os
    
    topdf_path = config.get('htmltopdf.path')
    
    fd_html, html_path = tempfile.mkstemp(suffix='.html', prefix='sapns_')
    os.close(fd_html)
    try:
        # save HTML content
        f_input = open(html_path, 'wb')
        try:
            f_input.write(html_content)
        
        finally:
            f_input.close()
        
        pdf_content = ''
        fd_pdf, pdf_path = tempfile.mkstemp(suffix='.pdf', prefix='sapns_')
        os.close(fd_pdf)
        try:
            sp.check_call([topdf_path, '-q', html_path, pdf_path])
            
            # get PDF content
            f_output = open(pdf_path, 'rb')
            try:
                pdf_content = f_output.read()
            
            finally:
                f_output.close()
            
        finally:
            if os.access(pdf_path, os.F_OK):
                os.remove(pdf_path)
        
    finally:
        if os.access(html_path, os.F_OK):
            os.remove(html_path)
    
    return pdf_content

def pagination(rp, pag_n, total):
        
    # total number of pages
    pos = (pag_n-1)*(rp or 0)
    total_pag = 1
    if rp > 0:
        total_pag = total/rp
        
        if total % rp != 0:
            total_pag += 1
        
        if total_pag == 0:
            total_pag = 1
    
    # rows in this page
    this_page = total - pos
    if rp and this_page > rp:
        this_page = rp
        
    return (this_page, total_pag,)