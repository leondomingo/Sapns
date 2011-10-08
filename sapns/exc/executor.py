# -*- coding: utf-8 -*-

import os
import sys
from argparse import ArgumentParser
from logging.config import fileConfig

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from paste.deploy import appconfig
from sapns.config.environment import load_environment

class Executor(object):

    def load_config(self, filename):
        conf = appconfig('config:' + os.path.abspath(filename))
        load_environment(conf.global_conf, conf.local_conf)
        fileConfig(os.path.abspath(filename))
    
    def parse_args(self):
        parser = ArgumentParser(description=__doc__)
        parser.add_argument("conf_file", help="configuration to use")
        return parser.parse_args()
    
    def execute(self, pkg_name, func_name, *args, **kwargs):
        _args = self.parse_args()
        self.load_config(_args.conf_file)
        
        m = __import__(pkg_name, fromlist=[func_name])
        func = getattr(m, func_name)
        if isinstance(func, type):
            # "func" is a class so arguments are passed to __init__ and then
            # "func" is executed
            func(*args, **kwargs)()
            
        else:
            # "func" is a function executed with the passed arguments
            func(*args, **kwargs)