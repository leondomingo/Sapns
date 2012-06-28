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
        
        tops = [('init', os.path.join(current_path, 'init'),)]
        
        root_folder = config.get('app.root_folder')
        if root_folder:
            tops.append((root_folder, os.path.join(current_path, root_folder),))
            
        def add_update(code):
            # save "update"
            new_u = SapnsUpdates()
            new_u.code = code
            #new_u.description =
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
                                            
                                            if hasattr(callable_obj, '__desc__'):
                                                
                                                desc__ = callable_obj.__desc__
                                                if not SapnsUpdates.by_code(desc__):
                                                    
                                                    logger.warning(u'[%s] Executing [%s.%s %s]' % (topid, m.__name__, member[0], desc__))
                                                    
                                                    if hasattr(callable_obj, '__call__'):
                                                        transaction.begin()
                                                        try:
                                                            callable_obj()
                                                            
                                                            add_update(desc__)
                                                            transaction.commit()
                                                            
                                                        except Exception, e:
                                                            logger.error(e)
                                                            transaction.abort()
                
                                                    else:
                                                        raise Exception('[%s] Class "%s.%s" in not callable' % (topid, m.__name__, member[0]))
                                                    
                                                else:
                                                    logger.warning(u'[%s] Skipping [%s.%s %s]' % (topid, m.__name__, member[0], desc__))
                                                
                                            else:
                                                logger.warning('[%s] PY: %s.%s lacks of "__desc__"' % (topid, m.__name__, member[0]))
                                        
                                        except Exception, e:
                                            logger.error(e)
                                            logger.info(name + ' ' + member[0])
                                            
                                    
                            except ImportError, e:
                                logger.warning(e)
                            
                        elif ext.lower() == '.sql':
                            f_sql = _open(os.path.join(dirpath, fn), 'rb', encoding='utf-8')
                            try:
                                sql_text = f_sql.read()
                                
                                m = re.search(r'^--\s*desc\:(.+)$', sql_text.split('\n')[0])
                                if m:
                                    desc__ = m.group(1).strip()
                                    
                                    if not SapnsUpdates.by_code(desc__):
                                        logger.info('[%s] %s: __desc__ = %s' % (topid, fn, desc__))
                                        
                                        for script in sql_text.split('--#'):
                                            if script.strip():
                                                
                                                transaction.begin()
                                                try:
                                                    dbs.execute(script.strip())
                                                    dbs.flush()
                                                    
                                                    add_update(desc__)
                                                    transaction.commit()
                                                    
                                                except Exception, e:
                                                    logger.error(e)
                                                    transaction.abort()

                                    else:
                                        logger.warning(u'[%s] Skipping [%s %s]' % (topid, fn, desc__))
    
                                else:
                                    logger.warning('[%s] SQL: %s lacks of "-- desc:" on first line' % (topid, name))
                                    
                            finally:
                                f_sql.close()

        
#        for u in TODO:
#            
#            u = Dict(**u)
#            if not SapnsUpdates.by_code(u.code):
#
#                logger.info(u'[%s] %s (%s)' % (u.code, u.desc or '', u.type.upper()))
#                
#                #dbs = Conexion(config.get('sqlalchemy.url')).session
#                transaction.begin()
#                try:
#                    # SQL
#                    if u.type.lower() == 'sql':
#                        #logger.info(_('Executing SQL script...'))
#                        f_sql = _open(os.path.join(current_path, u.filename), 'rb', 
#                                      encoding='utf-8')
#                        try:
#                            sql_text = f_sql.read()
#                            for script in sql_text.split('--#'):
#                                if script.strip():
#                                    dbs.execute(script.strip())
#                                    dbs.flush()
#                                
#                        finally:
#                            f_sql.close()
#
#                    # python
#                    elif u.type.lower() == 'py':
#                        #logger.info(_('Executing Python script...'))
#                        module_name = 'sapns.exc.update.%s' % u.module
#                        module_update = __import__(module_name, fromlist=['update'])
#                        
#                        _update = getattr(module_update, 'update')
#                        if isinstance(_update, type):
#                            # class
#                            _update()()
#                        
#                        else:
#                            # function
#                            _update()
#                        
#                    # save "update"
#                    new_u = SapnsUpdates()
#                    new_u.code = u.code
#                    new_u.description = u.desc
#                    new_u.exec_date = dt.datetime.now()
#                
#                    dbs.add(new_u)
#                    transaction.commit()
#                        
#                except Exception, e:
#                    transaction.abort()
#                    logger.error(e)
#                    
#            else:
#                logger.warning(u'Skipping [%s]' % u.code)