#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from argparse import ArgumentParser

import pylons
from contextlib import contextmanager
from pylons.i18n.translation import _get_translator

# this is a hook that is needed to set up some
# things that are needed inside transaction hooks
@contextmanager
def set_language_context_manager(language=None, **kwargs):
    # this is stolen from the pylons test setup.
    # it will make sure the gettext-stuff is working
    translator = _get_translator(language, **kwargs)
    pylons.translator._push_object(translator)
    try:
        yield
    finally:
        pylons.translator._pop_object()

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
    
    set_language_context_manager('en')
    
    args = parse_args()
    load_config(args.conf_file)
    
    update_metadata()

if __name__ == '__main__':
    do_init()