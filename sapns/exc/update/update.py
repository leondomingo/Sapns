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
        
        update_folder = config.get('app.update_folder', config.get('app.root_folder'))
        if update_folder:
            tops.append((update_folder, os.path.join(current_path, update_folder),))
            
        def add_update(code, description):
            # save "update"
            new_u = SapnsUpdates()
            new_u.code = code
            new_u.description = description
            new_u.exec_date = dt.datetime.now()
        
            dbs.add(new_u)
            dbs.flush()
            
        todo = []
        for topid, top in tops:
            for dirpath, _, filenames in os.walk(top):
                
                dirname = dirpath.split('/')[-1]
                
                if filenames != []:
                    for fn in sorted(filenames):
                        
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

                                                    if hasattr(callable_obj, '__call__'):
                                                        
                                                        todo.append(dict(type='py',
                                                                         path=os.path.join(dirpath, fn),
                                                                         code=code__,
                                                                         desc=desc__,
                                                                         callable=callable_obj,
                                                                         topid=topid,
                                                                         dirname=dirname,
                                                                         module_name=m.__name__,
                                                                         class_name=member[0],
                                                                         ))
                                                        
                                                    else:
                                                        raise Exception('[%s] Class "%s.%s" in not callable' % (topid, m.__name__, member[0]))
                                                    
                                                else:
                                                    logger.warning(u'[%s] Skipping [%s__%s.%s "%s"]' % (topid, dirname, m.__name__, member[0], code__))
                                                
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
                                
                                # -- __ignore__
                                m_ignore = re.search(r'^--\s*__ignore__\s*$', sql_text, re.M)
                                if m_ignore:
                                    logger.warning('[%s] SQL: ignoring "%s"' % (topid, fn))
                                    continue
                                
                                # -- __code__ = put here your code
                                m_code = re.search(r'^--\s*__code__\s+=\s+(.+)$', sql_text, re.M)
                                if m_code:
                                    code__ = m_code.group(1).strip()
                                    
                                    if not SapnsUpdates.by_code(code__):
                                        
                                        # -- __desc__ = put here your description
                                        desc__ = None
                                        m_desc = re.search(r'^--\s*__desc__\s+=\s+(.+)$', sql_text, re.M)
                                        if m_desc:
                                            desc__ = m_desc.group(1).strip()
                                            logger.info(desc__)
                                            
                                        todo.append(dict(type='sql',
                                                         path=os.path.join(dirpath, fn),
                                                         code=code__,
                                                         desc=desc__,
                                                         sql_text=sql_text,
                                                         topid=topid,
                                                         dirname=dirname,
                                                         ))
                                        
                                    else:
                                        logger.warning(u'[%s] Skipping [%s__%s "%s"]' % (topid, dirname, fn, code__))
    
                                else:
                                    logger.warning(u'[%s] SQL: Ignoring [%s__%s] cause lacks of "__code__"' % (topid, dirname, fn))
                                    
                            finally:
                                f_sql.close()
                                
        def _cmp(x, y):
            if 'init/' in x['path'] and 'init/' not in y['path']:
                return -1
            
            elif 'init/' not in x['path'] and 'init/' in y['path']:
                return 1
            
            else:
                return cmp(x['path'], y['path'])
            
        if todo:
            logger.info('TODO'.center(80, '-'))
        
        for update in sorted(todo, cmp=_cmp):
            if update['type'] == 'py':
                transaction.begin()
                try:
                    logger.warning(u'[%s] Executing [%s__%s.%s "%s"]' % (update['topid'], 
                                                                         update['dirname'],
                                                                         update['module_name'], 
                                                                         update['class_name'], 
                                                                         update['code']))
                    
                    # execute (call)
                    update['callable']()
                    
                    # register update
                    add_update(update['code'], update['desc'])
                    
                    transaction.commit()
                    
                except Exception, e:
                    logger.error(e)
                    transaction.abort()
                    
            elif update['type'] == 'sql':
                transaction.begin()
                try:
                    for script in update['sql_text'].split('--#'):
                        if script.strip():
                            
                            logger.warning(u'[%s] Executing [%s__%s "%s"] "%s..."' % (update['topid'], 
                                                                                      update['dirname'], 
                                                                                      os.path.basename(update['path']),
                                                                                      update['code'],
                                                                                      script.strip()[:30].replace('\n', ' '),
                                                                                      ))
                            
                            dbs.execute(script.strip())
                            dbs.flush()
                            
                    # register update
                    add_update(update['code'], update['desc'])
                
                    transaction.commit()
                                
                except Exception, e:
                    logger.error(e)
                    transaction.abort()
                    
                    
                    