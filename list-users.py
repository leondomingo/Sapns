#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Print all the usernames to the console. """
import os
import sys
from argparse import ArgumentParser
import re

from tg import config
from paste.deploy import appconfig
from sapns.config.environment import load_environment
from sapns.model import DBSession
from sapns.model.sapnsmodel import SapnsUser

def load_config(filename):
    conf = appconfig('config:' + os.path.abspath(filename))
    load_environment(conf.global_conf, conf.local_conf)

def parse_args():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("conf_file", help="configuration to use")
    parser.add_argument('--mode')

    return parser.parse_args()

def main():
    args = parse_args()
    print args.mode
    load_config(args.conf_file)
    
    print config.get('grid.date_format') #, default='%m/%d/%Y')
    
    m = re.search(r'://(\w+):(\w+)@(\w+)(:\d+)?/(\w+)', str(DBSession.bind))
    if m:
        user_name = m.group(1)
        psswd = m.group(2)
        host = m.group(3)
        port = m.group(4)
        db = m.group(5)
        
        print user_name, psswd, host, port or 5432, db

    for user in DBSession.query(SapnsUser).order_by(SapnsUser.user_id):
        print '%s %s [%s]' % (user.user_id, user.display_name, user.user_name)

if __name__ == '__main__':
    sys.exit(main())
