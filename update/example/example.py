# -*- coding: utf-8 -*-

from os.path import join, dirname, abspath
import sys

sapns_path = join(dirname(abspath(__file__)), '../..')
sys.path.append(sapns_path)

from paste.deploy import appconfig
from sapns.config.environment import load_environment
from sapns.model import DBSession
# more imports here...

def load_config(filename):
    conf = appconfig('config:' + abspath(filename))
    load_environment(conf.global_conf, conf.local_conf)

if __name__ == '__main__':
    load_config(sys.argv[1])
    # TODO: Updates here