# -*- coding: utf-8 -*-

import os
import re
import logging
import datetime as dt
import encodings
_open = encodings.codecs.open
from tg import config
from sapns.exc.conexion import Conexion
from sapns.model.sapnsmodel import SapnsUpdates
from neptuno.dict import Dict
from todo import TODO

logger = logging.getLogger('Update')
current_path = os.path.dirname(os.path.abspath(__file__))

class Update(object):
    
    def __init__(self):
        logger.info('Loading settings...')
        
        # postgresql://postgres:mypassword@localhost:5432/mydb
        m_session = re.search(r'://(\w+):(\w+)@(\w+)(:\d+)?/(\w+)', 
                              unicode(config.get('sqlalchemy.url')))
        if m_session:
            self.user = m_session.group(1)
            self.password = m_session.group(2)
            self.host = m_session.group(3)
            self.port = m_session.group(4)
            self.db = m_session.group(5)
            self.pg_path = config.get('pg_path', '/usr/bin/')
            
        else:
            raise Exception('It was not possible to get connection data')
        
    def __call__(self):
        
        for u in TODO:
            
            u = Dict(**u)
            if not SapnsUpdates.by_code(u.code):

                logger.info(u'[%s] %s (%s)' % (u.code, u.desc or '', u.type.upper()))
                
                dbs = Conexion(config.get('sqlalchemy.url')).session
                try:
                    # SQL
                    if u.type.lower() == 'sql':
                        #logger.info(_('Executing SQL script...'))
                        f_sql = _open(os.path.join(current_path, u.filename), 'rb', 
                                      encoding='utf-8')
                        try:
                            sql_text = f_sql.read()
                            for script in sql_text.split('--#'):
                                if script.strip():
                                    dbs.execute(script.strip())
                                    dbs.flush()
                                
                        finally:
                            f_sql.close()

                    # python
                    elif u.type.lower() == 'py':
                        #logger.info(_('Executing Python script...'))
                        module_name = 'sapns.exc.update.%s' % u.module
                        module_update = __import__(module_name, fromlist=['update'])
                        
                        _update = getattr(module_update, 'update')
                        if isinstance(_update, type):
                            _update(dbs)()
                        
                        else:
                            _update(dbs)
                        
                    # save "update"
                    new_u = SapnsUpdates()
                    new_u.code = u.code
                    new_u.description = u.desc
                    new_u.exec_date = dt.datetime.now()
                
                    dbs.add(new_u)
                    dbs.commit()
                        
                except Exception, e:
                    dbs.rollback()
                    logger.error(e)
                    
            else:
                logger.warning(u'Skipping [%s]' % u.code)