# -*- coding: utf-8 -*-

from sapns.model import SapnsClass
import logging

class CascadeDelete(object):
    
    def __init__(self, *args):
        self.args = args
    
    def __call__(self):
        _logger = logging.getLogger('CascadeDelete')
        class_ = SapnsClass.by_name(self.args[0].decode('utf-8'))
        _r = class_.cascade_delete(int(self.args[1]))
        #_logger.info(_r)