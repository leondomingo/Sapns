# -*- coding: utf-8 -*-

from pylons.i18n import ugettext as _, lazy_ugettext as l_

from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsClass, SapnsAction, SapnsAttribute

import logging
from sqlalchemy import MetaData
from sqlalchemy.sql.expression import and_
from sqlalchemy.types import INTEGER, NUMERIC, BIGINT, DATE, TEXT, VARCHAR,\
    BOOLEAN, BLOB
from sqlalchemy.dialects.postgresql.base import TIME, TIMESTAMP, BYTEA

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
            
        else:
            logger.warning('.....already exists')
            
        tables_id[tbl['name']] = klass.class_id
            
        # create an action
        def create_action(name, type_):
            action = dbs.query(SapnsAction).\
                        filter(and_(SapnsAction.class_id == klass.class_id,
                                    SapnsAction.type == type_)).\
                        first()
                            
            if not action:
                action = SapnsAction()
                action.name = name
                action.type = type_
                action.class_id = klass.class_id
                
                dbs.add(action)
                dbs.flush()
                
        # create standard actions
        create_action(unicode(l_('New')), SapnsAction.TYPE_NEW)
        create_action(unicode(l_('Edit')), SapnsAction.TYPE_EDIT)
        create_action(unicode(l_('Delete')), SapnsAction.TYPE_DELETE)
        create_action(unicode(l_('List')), SapnsAction.TYPE_LIST)
            
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