#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from argparse import ArgumentParser
from logging.config import fileConfig

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from paste.deploy import appconfig
from sapns.config.environment import load_environment

class Executor(object):
    
    def __init__(self, args=None):
        self.args = args

    def load_config(self, filename):
        conf = appconfig('config:' + os.path.abspath(filename))
        load_environment(conf.global_conf, conf.local_conf)
        fileConfig(os.path.abspath(filename))
    
    def parse_args(self):
        parser = ArgumentParser(description=__doc__)
        parser.add_argument("conf_file", help="configuration to use")
        return parser.parse_args()
    
    def execute(self, pkg_name, func_name, *args, **kwargs):
        if not self.args:
            conf_file = self.parse_args().conf_file
            
        else:
            conf_file = self.args.conf_file
            
        self.load_config(conf_file)
        
        m = __import__(pkg_name, fromlist=[func_name])
        func = getattr(m, func_name)
        if isinstance(func, type):
            # "func" is a class so arguments are passed to __init__ and then
            # "func" is executed
            func(*args, **kwargs)()
            
        else:
            # "func" is a function executed with the passed arguments
            func(*args, **kwargs)
            
if __name__ == '__main__':
    
    try:
        from executions import EXECUTIONS
    except ImportError:
        from executions_default import EXECUTIONS
    
    pr = ArgumentParser(description=__doc__)
    pr.add_argument("conf_file", help="configuration file")
    pr.add_argument('exc_id', help='execution identifier')
    pr.add_argument('extra_args', metavar='a', nargs='*', help='extra argument')
    _args = pr.parse_args()
    
    a = _args.extra_args
    kw = {}
    
    if EXECUTIONS.has_key(_args.exc_id):
        _pkg_name = EXECUTIONS[_args.exc_id][0]
        _func_name = EXECUTIONS[_args.exc_id][1]
        
        # *args
        if len(EXECUTIONS[_args.exc_id]) > 2:
            exc_args = EXECUTIONS[_args.exc_id][2]
            if exc_args: 
                a = a + list(exc_args) 
        
            # **kwargs
            if len(EXECUTIONS[_args.exc_id]) > 3:
                kw = EXECUTIONS[_args.exc_id][3]
        
        e = Executor(args=_args)
        e.execute(_pkg_name, _func_name, *a, **kw)
        
    else:
        sys.stderr.write('ERROR: It does not exist the execution with id "%s"\n' % _args.exc_id)