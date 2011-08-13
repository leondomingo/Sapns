# -*- coding: utf-8 -*-

import os
import sys
import re
import logging
import subprocess as sp
from pylons.i18n import ugettext as _
from tg import config
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUpdates
from neptuno.dict import Dict
from todo import TODO 

logger = logging.getLogger('Update.__call__')
current_path = ''

class Update(object):
    
    def __init__(self):
        logger.info(_('Loading settings...'))
        
        # postgresql://postgres:mypassword@localhost:5432/mydb
        m_session = re.search(r'://(\w+):(\w+)@(\w+)(:\d+)?/(\w+)', str(dbs.bind))
        if m_session:
            self.user = m_session.group(1)
            self.password = m_session.group(2)
            self.host = m_session.group(3)
            self.port = m_session.group(4)
            self.db = m_session.group(5)
            self.pg_path = config.get('pg_path', '/usr/bin/')
            
            logger.info('OK')
            
        else:
            raise Exception(_('It was not possible to get connection data'))
        
    def __call__(self):

        for u in TODO:
            
            u = Dict(**u)
            if not SapnsUpdates.by_code(u.code):

                # type of update
                if u.type.lower() == 'sql':
                    logger.info(_('Executing SQL script...'))
                    os.environ['PGPASSWORD'] = self.password
                    
                    call = [os.path.join(self.pg_path, 'psql'),
                            '-h', self.host, 
                            '-U', self.user, 
                            '-d', self.db,
                            '-f', os.path.join(current_path, u.filename)]
                    
                    if self.port:
                        call.append('-p')
                        # ":<port>"
                        call.append(self.port[1:])
                    
                    sp.check_call(call)
                
                elif u.type.lower() == 'py':
                    logger.info(_('Executing Python script...'))
                    module = __import__(u.module, None, None, ['update'])
                    module.update()
                    
            else:
                logger.warning(_('Skipping [%s]' % u.code))