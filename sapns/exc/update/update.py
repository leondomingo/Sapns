# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUpdates
from tg import config
import datetime as dt
import encodings
import inspect
import logging
import os
import re
import transaction
_open = encodings.codecs.open

logger = logging.getLogger('Update')
current_path = os.path.dirname(os.path.abspath(__file__))

class Update(object):
    
    def __init__(self):
        logger.info('Loading settings...')
        
        # postgresql://postgres:mypassword@localhost:5432/mydb
        m_session = re.search(r'://(\w+):(\w+)@(\w+)(:\d+)?/(\w+)', unicode(config.get('sqlalchemy.url')))
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
        
        tops = [('sapns', os.path.join(current_path, 'init'),)]
        
        root_folder = config.get('app.root_folder')
        if root_folder:
            tops.append((root_folder, os.path.join(current_path, root_folder),))
            
        def add_update(code, description):
            # save "update"
            new_u = SapnsUpdates()
            new_u.code = code
            new_u.description = description
            new_u.exec_date = dt.datetime.now()
        
            dbs.add(new_u)
            dbs.flush()
            
        for topid, top in tops:
            for dirpath, _, filenames in os.walk(top):
                if filenames != []:
                    for fn in filenames:
                        name, ext = os.path.splitext(fn)
                        if ext.lower() == '.py' and name != '__init__':
                            
                            relative_path = os.path.join(dirpath.replace(current_path, ''), name).split('/')[1:]
                            relative_path = 'sapns.exc.update.%s' % ('.'.join(relative_path))
                            try:
                                m = __import__(relative_path, fromlist=[''])
                                
                                for member in inspect.getmembers(m, inspect.isclass):
                                    if member[1].__module__ == relative_path and member[0] != 'update':
                                        try:
                                            cls = getattr(m, member[0])
                                            if cls.__base__.__name__ != 'object':
                                                continue
                                            
                                            callable_obj = cls()
                                            
                                            code__ = getattr(callable_obj, '__code__', None)
                                            if code__:
                                                
                                                if not SapnsUpdates.by_code(code__):
                                                    
                                                    desc__ = getattr(callable_obj, '__desc__', None)
                                                    
                                                    logger.warning(u'[%s] Executing [%s.%s "%s"]' % (topid, m.__name__, member[0], code__))
                                                    
                                                    if hasattr(callable_obj, '__call__'):
                                                        transaction.begin()
                                                        try:
                                                            callable_obj()
                                                            
                                                            add_update(code__, desc__)
                                                            transaction.commit()
                                                            
                                                        except Exception, e:
                                                            logger.error(e)
                                                            transaction.abort()
                
                                                    else:
                                                        raise Exception('[%s] Class "%s.%s" in not callable' % (topid, m.__name__, member[0]))
                                                    
                                                else:
                                                    logger.warning(u'[%s] Skipping [%s.%s "%s"]' % (topid, m.__name__, member[0], code__))
                                                
                                            else:
                                                logger.warning('[%s] PY: %s.%s lacks of "__code__"' % (topid, m.__name__, member[0]))
                                        
                                        except Exception, e:
                                            logger.error(e)
                                            logger.info(name + ' ' + member[0])
                                            
                                    
                            except ImportError, e:
                                logger.warning(e)
                            
                        elif ext.lower() == '.sql':
                            f_sql = _open(os.path.join(dirpath, fn), 'rb', encoding='utf-8')
                            try:
                                sql_text = f_sql.read()
                                
                                m_code = re.search(r'^--\s*code\:(.+)$', sql_text, re.M)
                                if m_code:
                                    code__ = m_code.group(1).strip()
                                    
                                    if not SapnsUpdates.by_code(code__):
                                        
                                        desc__ = None
                                        m_desc = re.search(r'^--\s*desc\:(.+)$', sql_text, re.M)
                                        if m_desc:
                                            desc__ = m_desc.group(1).strip()
                                            logger.info(desc__)
                                            
                                        continue
                                        
                                        logger.info('[%s] %s: __code__ = "%s"' % (topid, fn, code__))
                                        
                                        for script in sql_text.split('--#'):
                                            if script.strip():
                                                
                                                transaction.begin()
                                                try:
                                                    dbs.execute(script.strip())
                                                    dbs.flush()
                                                    
                                                    add_update(code__, desc__)
                                                    transaction.commit()
                                                    
                                                except Exception, e:
                                                    logger.error(e)
                                                    transaction.abort()

                                    else:
                                        logger.warning(u'[%s] Skipping [%s "%s"]' % (topid, fn, code__))
    
                                else:
                                    logger.warning('[%s] SQL: %s lacks of "-- code:"' % (topid, name))
                                    
                            finally:
                                f_sql.close()