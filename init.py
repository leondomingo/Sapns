#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from argparse import ArgumentParser

#from tg import config
#from sapns.model import DBSession as dbs
from paste.deploy import appconfig
from sapns.config.environment import load_environment

from sapns.lib.sapns.util import update_metadata

def load_config(filename):
    conf = appconfig('config:' + os.path.abspath(filename))
    load_environment(conf.global_conf, conf.local_conf)

def parse_args():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('conf_file', help='configuration to use')

    return parser.parse_args()

def do_init():
    args = parse_args()
    load_config(args.conf_file)
    
    update_metadata()

if __name__ == '__main__':
    do_init()