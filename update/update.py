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

import pylons
from pylons.i18n import ugettext as _
from pylons.i18n.translation import _get_translator
from contextlib import contextmanager

@contextmanager
def set_language_context_manager(language=None, **kwargs):
    translator = _get_translator(language, **kwargs)
    pylons.translator._push_object(translator)
    try:
        yield
    finally:
        pylons.translator._pop_object()
        
@contextmanager
def set_tmpl_context_cm():
    obj = None
    pylons.tmpl_context._push_object(obj)
    try:
        yield
    finally:
        pylons.tmpl_context._pop_object()

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
    parser.add_argument('-l', '--lang', help='language')

    return parser.parse_args()

def make_update(args, mode):
    
    sys.stdout.write(_('Loading settings...'))
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
        raise Exception(_('It was not possible to get connection data'))
    
    SETTINGS['pg_path'] = config.get('pg_path', '/usr/bin/')
    
    if not mode.lower() in ['pre', 'post']:
        raise Exception(_('"%s": Wrong mode' % mode))

    sys.stdout.write(_('Updating in [%s] mode\n' % mode))

    # read already-done updates
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
            # # a comment
            # #7000 pre
            m_coment = re.search(r'^#.+', line)
            if m_coment:
                continue

            # 7916.modelo    post    issue_7916/issue_7916.sql
            # 7916-otros     post    issue_7916.issue_7916  .py
            m_issue = re.search(r'^([\w\-\._]+)\s+(pre|post)\s+([\w./-]+)\s*(\.py)?', 
                                line, re.I | re.U)
            if m_issue:
                # 6729    post    ./issue_6729/issue_6729.sql
                # ===========================================
                # 6729 post
                current_issue = '%s %s' % (m_issue.group(1), m_issue.group(2))
                
                if current_issue in made or \
                m_issue.group(2).lower() != mode.lower():
                    sys.stderr.write(_('Skipping [%s] \n' % current_issue))

                else:
                    sys.stdout.write('[%s] ' % current_issue)
                    
                    # get update file extension
                    ext = os.path.splitext(m_issue.group(3))[1]
                    try:
                        # .py
                        if m_issue.group(4):
                            try:
                                # Python
                                sys.stdout.write(_('Executing Python script...\n'))
                                module = __import__(m_issue.group(3), None, None, ['update'])
                                module.update()
                                
                            except Exception:
                                raise Exception('[%s] failed!' % current_issue)

                        # SQL
                        elif ext == '.sql':
                            sys.stdout.write(_('Executing SQL script...\n'))
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
                        sys.stderr.write('%s\n' % e)

    finally:
        f_todo.close()
        f_done.close()
            
if __name__ == '__main__':
    
    args = parse_args()
    mode = args.mode or 'post'
    load_config(args.conf_file)
    
    import logging.config
    logging.config.fileConfig(args.conf_file)

    with set_tmpl_context_cm():
        with set_language_context_manager(language=args.lang):    
            make_update(args, mode)