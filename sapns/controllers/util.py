# -*- coding: utf-8 -*-
"""Views management controller"""

# turbogears imports
from tg import expose, url

# third party imports
#from pylons.i18n import ugettext as _
#from repoze.what import predicates

# project specific imports
from sapns.lib.base import BaseController
from sqlalchemy.schema import MetaData
from sapns.model import DBSession
#from sapns.model import DBSession, metadata

import logging
from sqlalchemy.types import INTEGER, NUMERIC, BIGINT, DATE, TEXT, VARCHAR,\
    BOOLEAN, BLOB
from sqlalchemy.dialects.postgresql.base import TIME, TIMESTAMP, BYTEA

class UtilController(BaseController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = authorize.not_anonymous()
    
    @expose('util/index.html')
    def index(self, came_from='/'):
        return dict(page='util', came_from=came_from)
    
    @expose('util/tables.html')
    def extract_model(self):
        
        logger = logging.getLogger(__name__ + '/extract_model')
        
        meta = MetaData(bind=DBSession.bind, reflect=True)
        logger.info(meta.bind)
        
        tables = []
        for tbl in sorted(meta.sorted_tables, 
                          # table name alphabetical order
                          cmp=lambda x,y: cmp(x.name, y.name)):
            
            if not tbl.name.startswith('sp_'):
                
                logger.info('Table: %s' % tbl.name)
                
                t = dict(name=tbl.name,
                         columns=[]
                         )
                
                fk_cols = []
                fk_tables = []
                for fk in tbl.foreign_keys:
                    logger.info(fk.parent)
                    fk_tables.append(fk.column.table)
                    fk_cols.append(fk.parent.name)
                    
                for c in tbl.columns:
                    col = dict(name=c.name, type=c.type, fk='-')
                    
                    logger.info('%s' % type(c.type))
                    
                    type_name = '---'
                    if isinstance(c.type, INTEGER):
                        type_name = 'integer'
                        
                    elif isinstance(c.type, NUMERIC):
                        type_name = 'numeric'
                        
                    elif isinstance(c.type, BIGINT):
                        type_name = 'bigint'

                    elif isinstance(c.type, DATE):
                        type_name = 'date'
                        
                    elif isinstance(c.type, TIME):
                        type_name = 'time'
                        
                    elif isinstance(c.type, TIMESTAMP):
                        type_name = 'timestamp'

                    elif isinstance(c.type, VARCHAR):
                        type_name = 'string'
                        
                    elif isinstance(c.type, TEXT):
                        type_name = 'text'
                        
                    elif isinstance(c.type, BOOLEAN):
                        type_name = 'boolean'
                        
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