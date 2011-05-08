#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import subprocess as sp
from config import CONFIG
sys.path = sys.path + CONFIG['paths']
from nucleo.config import CONFIGURACION

current_path = os.path.dirname(os.path.abspath(__file__))

def actualizar(modo='post'):
    
    if not modo.lower() in ['pre', 'post']:
        raise Exception('Modo "%s" incorrecto' % modo)

    sys.stdout.write('Actualizando en modo [%s]\n' % modo)

    # leer actualizaciones realizadas
    # 6729 post
    # 7832 pre
    # ...
    
    DONE = os.path.join(current_path, 'DONE')
    TODO = os.path.join(current_path, 'TODO')
    
    realizados = []
    if os.path.exists(DONE):
        f_done = file(DONE, 'rb')
        try:
            for linea in f_done:
                m_issue = re.search(r'^([\w./-]+)\s+(pre|post)', linea)
                if m_issue:
                    # 6729 post
                    current_issue = '%s %s' % (m_issue.group(1),
                                               m_issue.group(2))
                    
                    if m_issue.group(2) == modo.lower() and \
                    current_issue not in realizados:
                        # 6729 post
                        realizados.append('%s %s' % (m_issue.group(1), 
                                                     m_issue.group(2)))

        finally:
            f_done.close()

    # realizar actualizaciones pendientes
    # actualizaciones a realizar
    f_todo = file(TODO, 'rb')
    
    # actualizaciones realizadas
    f_done = file(DONE, 'a')
    try:
        for linea in f_todo:
            # # esto es un comentario
            # #7000 pre
            m_coment = re.search(r'^#.+', linea)
            if m_coment:
                continue

            # 7916.modelo    post    ./issue_7916/issue_7916.sql
            # 7916-otros     post    ./issue_7916/issue_7916.py
            m_issue = re.search(r'^([\w\-\._]+)\s+(pre|post)\s+([\w./-]+)', 
                                linea, re.I | re.U)
            if m_issue:
                # 6729    post    ./issue_6729/issue_6729.sql
                # ===========================================
                # 6729 post
                current_issue = '%s %s' % (m_issue.group(1), 
                                           m_issue.group(2))
                
                if current_issue in realizados or \
                m_issue.group(2).lower() != modo.lower():
                    sys.stderr.write('Saltando actualización [%s] \n' % current_issue)

                else:
                    sys.stdout.write('Actualizando [%s]\n' % current_issue)
                    
                    # obtener extensión del fichero de actualización
                    ext = os.path.splitext(m_issue.group(3))[1]
                    try:
                        if ext == '.py':
                            # ejecutar Python
                            sys.stdout.write('Ejecutando Python...\n')
                            sp.check_call([sys.executable, 
                                           os.path.join(current_path,
                                                        m_issue.group(3))])

                        elif ext == '.sql':
                            # ejecutar SQL
                            sys.stdout.write('Ejecutando SQL...\n')
                            os.environ['PGPASSWORD'] = CONFIGURACION['password']
                            sp.check_call([os.path.join(CONFIG['pg_path'], 'psql'),
                                           '-h', CONFIGURACION['host'], 
                                           '-U', CONFIGURACION['user'],
                                           '-d', CONFIGURACION['db'],
                                           '-f', os.path.join(current_path,
                                                              m_issue.group(3))])

                        # registrar en fichero de actualizaciones realizadas
                        f_done.write('%s\n' % current_issue)

                    except Exception, e:
                        sys.stderr.write(str(e))

    finally:
        f_todo.close()
        f_done.close()

if __name__ == '__main__':
    modo = 'post'
    if len(sys.argv) > 1:
        modo = sys.argv[1]

    actualizar(modo)