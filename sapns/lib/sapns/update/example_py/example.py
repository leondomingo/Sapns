# -*- coding: utf-8 -*-

import sys
from sapns.model import DBSession as dbs #@UnusedImport

class Example(object):
    
    def __call__(self):
        sys.stdout.write('This is an example\n')
        #raise Exception('Exception in the example')
        
update = Example()