# -*- coding: utf-8 -*-

from jinja2 import Environment, FileSystemLoader
from neptuno.dict import Dict
from sapns.exc.conexion import Conexion
from sapns.model.sapnsmodel import SapnsClass, SapnsPermission, SapnsAttribute, \
    SapnsUser, SapnsShortcut, SapnsAttrPrivilege, SapnsRole, SapnsUserRole, \
    SapnsPrivilege
from sqlalchemy import MetaData
from sqlalchemy.dialects.postgresql.base import TIME, TIMESTAMP, BYTEA
from sqlalchemy.sql.expression import and_
from sqlalchemy.types import INTEGER, NUMERIC, BIGINT, DATE, TEXT, VARCHAR, \
    BOOLEAN, BLOB
from tg import config
import logging
import os

ROLE_MANAGERS = u'managers'
current_path = os.path.dirname(os.path.abspath(__file__))

class InitSapns(object):
    
    def __init__(self):
        self.dbs = Conexion(config.get('sqlalchemy.url')).session
        
    def __call__(self):
        logger = logging.getLogger('InitSapns')
        
        logger.info('update_metadata')
        self.update_metadata()
        self.dbs.commit()
        
        logger.info('create_data_exploration')
        self.create_data_exploration()
        self.dbs.commit()

    def extract_model(self, all_=False):
        logger = logging.getLogger('lib.sapns.extract_model')
        
        dbs = self.dbs
        
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
            
            if not tbl.name.startswith('sp_') or all_:
                
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
                    col = Dict(name=c.name, type=repr(c.type), fk='-',
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
                        
                    except Exception:
                        col['fk_table'] = None
                        
                    t['columns'].append(col)
                    
                tables.append(t)
                
        return tables
            
    def update_metadata(self):
        
        logger = logging.getLogger('lib.sapns.update_metadata')
        
        dbs = self.dbs
        
        env = Environment(loader=FileSystemLoader(current_path))
        
        managers = dbs.query(SapnsRole).\
            filter(SapnsRole.group_name == u'managers').\
            first()
                
        tables = self.extract_model(all_=True)
        tables_id = {}
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
                klass.description =  u'Clases: %s' % tbl['name']
                
                dbs.add(klass)
                dbs.flush()
                
                # grant access (r/w) to "managers"
                priv = SapnsPrivilege()
                priv.role_id = managers.group_id
                priv.class_id = klass.class_id
                priv.granted = True
                
                dbs.add(priv)
                dbs.flush()
                
            else:
                logger.warning('.....already exists')
                
            tables_id[tbl['name']] = klass #.class_id
            
        tmpl = env.get_template('trigger_function_log.txt')
        
        pending_attr = {}
        for tbl in tables:
            
            #tables_id[tbl['name']] = klass.class_id
            klass = tables_id[tbl['name']]
                
            # create an action
            def create_action(name, type_):
                action = dbs.query(SapnsPermission).\
                    filter(and_(SapnsPermission.class_id == klass.class_id,
                                SapnsPermission.type == type_)).\
                    first()
                                
                if not action:
                    action = SapnsPermission()
                    action.permission_name = u'%s#%s' % (klass.name, name.lower())
                    action.display_name = name
                    action.type = type_
                    action.class_id = klass.class_id
                    
                    dbs.add(action)
                    dbs.flush()
                    
                    # add this action to "managers" role
                    managers.permissions_.append(action)
                    dbs.flush()
                    
                elif action.type == SapnsPermission.TYPE_LIST:
                    for s in action.shortcuts:
                        s.title = action.class_.title
                        dbs.add(s)
                        dbs.flush()
                    
            # create standard actions
            create_action(u'New', SapnsPermission.TYPE_NEW)
            create_action(u'Edit', SapnsPermission.TYPE_EDIT)
            create_action(u'Delete', SapnsPermission.TYPE_DELETE)
            create_action(u'List', SapnsPermission.TYPE_LIST)
            create_action(u'Docs', SapnsPermission.TYPE_DOCS)
                
            log_attributes = Dict(created=False, updated=False)
            log_cols = []
            first_ref = False
            for i, col in enumerate(tbl['columns']):
                
                logger.info('Column: %s' % col['name'])
                
                attr = dbs.query(SapnsAttribute).\
                    filter(and_(SapnsAttribute.name == col['name'],
                                SapnsAttribute.class_id == klass.class_id, 
                                )).\
                    first()
                    
                # log attributes
                if col['name'] in ['_created', '_updated']:
                    
                    if col['name'] == '_created':
                        log_attributes.created = True
                        
                    if col['name'] == '_updated':
                        log_attributes.updated = True
                    
                    continue
                
                elif col['name'] != 'id':
                    log_cols.append(col['name'])
                        
                if col['name'] not in ['id', '_created', '_updated']:
                    if not attr: 
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
                        
                        if attr.type == SapnsAttribute.TYPE_INTEGER and \
                        not attr.name.startswith('id_'):
                            # signed
                            attr.field_regex = r'^\s*(\+|\-)?\d+\s*$'
                            
                        elif attr.type == SapnsAttribute.TYPE_FLOAT:
                            # signed
                            # col['prec']
                            # col['scale']
                            attr.field_regex = r'^\s*(\+|\-)?\d{1,%d}(\.\d{1,%d})?\s*$' % \
                                (col['prec']-col['scale'],
                                 col['scale'])
                                
                        elif attr.type == SapnsAttribute.TYPE_TIME:
                            attr.field_regex = r'^\s*([01][0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?\s*$'
                        
                        dbs.add(attr)
                        dbs.flush()
                        
                        # grant access (r/w) to managers
                        priv = SapnsAttrPrivilege()
                        priv.role_id = managers.group_id
                        priv.attribute_id = attr.attribute_id
                        priv.access = SapnsAttrPrivilege.ACCESS_READWRITE
                        
                        dbs.add(priv)
                        dbs.flush()
                        
                    else:
                        logger.warning('.....already exists')
                        
                        # fill the "field_regex"
                        if attr and not attr.field_regex:
                            if attr.type == SapnsAttribute.TYPE_INTEGER and \
                            not attr.name.startswith('id_'):
                                # signed
                                attr.field_regex = r'^\s*(\+|\-)?\d+\s*$'
                                
                            elif attr.type == SapnsAttribute.TYPE_FLOAT:
                                # signed
                                attr.field_regex = r'^\s*(\+|\-)?\d{1,%d}(\.\d{1,%d})?\s*$' % \
                                    (col['prec'] - col['scale'], col['scale'])
                                    
                            elif attr.type == SapnsAttribute.TYPE_TIME:
                                attr.field_regex = r'^\s*([01][0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?\s*$'
                    
                # foreign key
                if col['fk_table'] != None:
                    pending_attr[attr.attribute_id] = col['fk_table'].name
                    
            if tbl['name'] != u'sp_logs':
                
                _log_attributes = []
                
                # _created
                if not log_attributes.created:
                    _log_attributes.append('ADD _created TIMESTAMP')
                
                # _updated
                if not log_attributes.updated:
                    _log_attributes.append('ADD _updated TIMESTAMP')
                    
                if _log_attributes:
                    _alter = 'ALTER TABLE %s %s;' % (tbl['name'], ', '.join(_log_attributes))
                    logger.info(_alter)
                    
                    try:
                        dbs.execute(_alter)
                        dbs.flush()
                        
                    except Exception, e:
                        #dbs.rollback()
                        logger.error(e)
                        
                # log trigger function
                try:
                    logf = tmpl.render(tbl_name=tbl['name'], cols=log_cols,
                                       class_id=klass.class_id,
                                       )
                    #logger.info(logf)
                    dbs.execute(logf)
                    dbs.flush()
                    
                except Exception, e:
                    #dbs.rollback()
                    logger.error(e)
                            
                # log triggers
                log_trigger = 'SELECT COUNT(*) FROM pg_trigger WHERE tgname = \'zzzflog_%s\'' % tbl['name']
                lt = dbs.execute(log_trigger).fetchone()
                if lt[0] == 0:
                    _trigger = '''create trigger zzzflog_%s
                                  after insert or update or delete
                                  on %s
                                  for each row
                                  execute procedure flog_%s();''' % ((tbl['name'],)*3)
                                  
                    #logger.info(_trigger)
                    try:
                        dbs.execute(_trigger)
                        dbs.flush()
                        
                    except Exception, e:
                        #dbs.rollback()
                        logger.error(e)
                    
            # update related classes
            for attr_id, fk_table in pending_attr.iteritems():
                attr = dbs.query(SapnsAttribute).get(attr_id)
                attr.related_class_id = tables_id[fk_table].class_id
            
                dbs.add(attr)
                dbs.flush()
        
    def create_dashboards(self, us):
        
        logger = logging.getLogger('lib.sapns.util.create_dashboards')
        
        dbs = self.dbs
            
        logger.info('Creating dashboard for "%s"' % us.display_name)
        
        # user's dashboard
        dboard = us.get_dashboard()
        if not dboard:
            
            dboard = SapnsShortcut()
            dboard.user_id = us.user_id
            dboard.parent_id = None
            dboard.title = u'Dashboard'
            dboard.order = 0
            
            dbs.add(dboard)
            dbs.flush()
            
            # data exploration
            
            data_ex = SapnsShortcut()
            data_ex.title = u'Data exploration'
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
            sc_project.title = config.get('app.name', u'Project')
            sc_project.parent_id = data_ex.shortcut_id
            sc_project.user_id = us.user_id
            sc_project.order = 1
            
            dbs.add(sc_project)
            dbs.flush()
            
        else:
            logger.info('Dashboard already exists')
            
    def create_data_exploration(self):
        
        dbs = self.dbs
        
        managers = SapnsRole.by_name(ROLE_MANAGERS)
        #managers = SapnsRole()
        
        logger = logging.getLogger('lib.sapns.util.create_data_exploration')
        
        tables = self.extract_model(all_=True)
    
        for us in dbs.query(SapnsUser).\
            join((SapnsUserRole,
                  and_(SapnsUserRole.user_id == SapnsUser.user_id,
                       SapnsUserRole.role_id == managers.group_id,
                       ))):
            
            self.create_dashboards(us)
            
            data_ex = us.get_dataexploration()
            sc_sapns = None
            sc_project = None
            if data_ex:
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
                    act_table.permission_name = u'%s#%s' % (cls.name, SapnsPermission.TYPE_LIST)
                    act_table.display_name = u'List'
                    act_table.type = SapnsPermission.TYPE_LIST
                    act_table.class_id = cls.class_id
                    
                    dbs.add(act_table)
                    dbs.flush()
                    
                    # add to "managers" role
                    managers.permissions_.append(act_table)
                    dbs.flush()
                    
                # project
                sc_parent = sc_project
                if cls.name.startswith('sp_'):
                    # sapns
                    sc_parent = sc_sapns
                    
                if sc_parent:
                    sc_table = dbs.query(SapnsShortcut).\
                        filter(and_(SapnsShortcut.parent_id == sc_parent.shortcut_id,
                                    SapnsShortcut.permission_id == act_table.permission_id,
                                    SapnsShortcut.user_id == us.user_id,
                                    )).\
                        first()
                            
                    # does this user have this class shortcut?
                    if not sc_table:
                        sc_table = SapnsShortcut()
                        sc_table.title = tbl['name']
                        sc_table.parent_id = sc_parent.shortcut_id
                        sc_table.user_id = us.user_id
                        sc_table.permission_id = act_table.permission_id
                        sc_table.order = i
            
                        dbs.add(sc_table)
                        dbs.flush()
                    
                    else:
                        logger.info(u'Shortcut for "%s" already exists' % cls.title)
                    
            # sort (alphabetically) shortcuts inside "data exploration"
            if sc_project:
                logger.info('Sorting shortcuts inside "data exploration"')
                i = 0
                for sc in dbs.query(SapnsShortcut).\
                        filter(SapnsShortcut.parent_id == sc_project.shortcut_id).\
                        order_by(SapnsShortcut.title):
                    
                    sc.order = i
                    dbs.add(sc)
                    dbs.flush()
                    
                    i += 1