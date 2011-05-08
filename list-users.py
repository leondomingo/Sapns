#!/usr/bin/env python
""" Print all the usernames to the console. """
import os
import sys
from argparse import ArgumentParser

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

    return parser.parse_args()

def main():
    args = parse_args()
    load_config(args.conf_file)

    for user in DBSession.query(SapnsUser).order_by(SapnsUser.user_id):
        print '%s %s [%s]' % (user.user_id, user.display_name, user.user_name)

if __name__ == '__main__':
    sys.exit(main())
