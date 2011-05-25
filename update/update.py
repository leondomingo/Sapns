#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import subprocess as sp
from argparse import ArgumentParser

current_path = os.path.dirname(os.path.abspath(__file__))
upper_path = os.path.split(current_path)[0]
sys.path.append(upper_path)

from tg import config
from paste.deploy import appconfig
from sapns.model import DBSession as dbs
from sapns.config.environment import load_environment

def load_config(filename):
    conf = appconfig('config:' + os.path.abspath(filename))
    load_environment(conf.global_conf, conf.local_conf)

def parse_args():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('conf_file', help='configuration to use')
    parser.add_argument('-m', '--mode')

    return parser.parse_args()

def make_update():
    
    args = parse_args()
    mode = args.mode or 'post'
    load_config(args.conf_file)

    sys.stdout.write('Loading settings...')
    SETTINGS = {}
    # postgresql://postgres:mypassword@localhost:5432/mydb
    m_session = re.search(r'://(\w+):(\w+)@(\w+)(:\d+)?/(\w+)', str(dbs.bind))
    if m_session:
        SETTINGS['user'] = m_session.group(1)
        SETTINGS['password'] = m_session.group(2)
        SETTINGS['host'] = m_session.group(3)
        SETTINGS['port'] = m_session.group(4)
        SETTINGS['db'] = m_session.group(5)
        
        sys.stdout.write('OK\n')
        
    else:
        raise Exception('It was not possible to get connection data!')
    
    SETTINGS['pg_path'] = config.get('pg_path', '/usr/bin/')
    
    if not mode.lower() in ['pre', 'post']:
        raise Exception('"%s": Wrong mode' % mode)

    sys.stdout.write('Updating in [%s] mode\n' % mode)

    # read already-made updates
    # 6729 post
    # 7832 pre
    # ...
    
    DONE = os.path.join(current_path, 'DONE')
    TODO = os.path.join(current_path, 'TODO')
    
    made = []
    if os.path.exists(DONE):
        f_done = file(DONE, 'rb')
        try:
            for line in f_done:
                m_issue = re.search(r'^([\w./-]+)\s+(pre|post)', line)
                if m_issue:
                    # 6729 post
                    current_issue = '%s %s' % (m_issue.group(1), m_issue.group(2))
                    
                    if m_issue.group(2) == mode.lower() and \
                    current_issue not in made:
                        # 6729 post
                        made.append('%s %s' % (m_issue.group(1), m_issue.group(2)))

        finally:
            f_done.close()

    # updates to be done
    f_todo = file(TODO, 'rb')
    
    # already-done updates
    f_done = file(DONE, 'a')
    try:
        for line in f_todo:
            # # esto es un comentario
            # #7000 pre
            m_coment = re.search(r'^#.+', line)
            if m_coment:
                continue

            # 7916.modelo    post    ./issue_7916/issue_7916.sql
            # 7916-otros     post    ./issue_7916/issue_7916.py
            m_issue = re.search(r'^([\w\-\._]+)\s+(pre|post)\s+([\w./-]+)', 
                                line, re.I | re.U)
            if m_issue:
                # 6729    post    ./issue_6729/issue_6729.sql
                # ===========================================
                # 6729 post
                current_issue = '%s %s' % (m_issue.group(1), m_issue.group(2))
                
                if current_issue in made or \
                m_issue.group(2).lower() != mode.lower():
                    sys.stderr.write('Skipping [%s] \n' % current_issue)

                else:
                    sys.stdout.write('[%s] ' % current_issue)
                    
                    # get update file extension
                    ext = os.path.splitext(m_issue.group(3))[1]
                    try:
                        if ext == '.py':
                            # Python
                            sys.stdout.write('Executing Python script...\n')
                            
                            call = [sys.executable, 
                                    os.path.join(current_path, m_issue.group(3)),
                                    args.conf_file,
                                    ]
                            
                            sp.check_call(call)

                        elif ext == '.sql':
                            # SQL
                            sys.stdout.write('Executing SQL script...\n')
                            os.environ['PGPASSWORD'] = SETTINGS['password']
                            
                            call = [os.path.join(SETTINGS['pg_path'], 'psql'),
                                    '-h', SETTINGS['host'], 
                                    '-U', SETTINGS['user'],
                                    '-d', SETTINGS['db'],
                                    '-f', os.path.join(current_path, m_issue.group(3))]
                            
                            if SETTINGS['port']:
                                call.append('-p')
                                # ":<port>"
                                call.append(SETTINGS['port'][1:])
                            
                            sp.check_call(call)
                            
                        # register update
                        f_done.write('%s\n' % current_issue)

                    except Exception, e:
                        sys.stderr.write(str(e))

    finally:
        f_todo.close()
        f_done.close()

if __name__ == '__main__':
    make_update()