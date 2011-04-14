# -*- coding: utf-8 -*-
"""Views management controller"""

# turbogears imports
from tg import expose, url, response, redirect

# third party imports
from pylons.i18n import ugettext as _
from repoze.what import authorize, predicates

# project specific imports
from sapns.lib.base import BaseController
from sqlalchemy.schema import MetaData
from sapns.model import DBSession, metadata

import logging
from sqlalchemy.types import INTEGER, NUMERIC, BIGINT, DATE, TEXT, VARCHAR,\
    BOOLEAN, BLOB
from sqlalchemy.dialects.postgresql.base import TIME, TIMESTAMP, BYTEA
from pylons.templating import render_jinja2
from sapns.model.sapnsmodel import SapnsClass, SapnsAttribute
from sqlalchemy.sql.expression import and_

class UtilController(BaseController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = authorize.not_anonymous()
    
    @expose('util/index.html')
    def index(self, came_from='/'):
        return dict(page='util', came_from=came_from)
    
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
                klass.description = 'Class: %s' % tbl['name']
                
                DBSession.add(klass)
                DBSession.flush()
                
            else:
                logger.warning('.....already exists')
                
            for i, col in enumerate(tbl['columns']):
                
                logger.info('Column: %s' % col['name'])
                
                atr = DBSession.query(SapnsAttribute).\
                        filter(and_(SapnsAttribute.name == col['name'],
                                    SapnsAttribute.class_id == klass.class_id, 
                                    )).\
                        first()
                        
                if not atr and col['name'] != id:
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
    def extract_model(self):
        
        logger = logging.getLogger(__name__ + '/extract_model')
        
        meta = MetaData(bind=DBSession.bind, reflect=True)
        logger.info('Connected to "%s"' % meta.bind)
        
        tables = []
        for tbl in sorted(meta.sorted_tables, 
                          # table name alphabetical order
                          cmp=lambda x,y: cmp(x.name, y.name)):
            
            if not tbl.name.startswith('sp_'):
                
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