# -*- coding: utf-8 -*-
"""Utilities controller"""

from pylons.i18n import ugettext as _
from pylons.templating import render_jinja2
from sapns.lib.base import BaseController
from tg import expose, url, response, predicates
import re
import sapns.lib.sapns.util as libutil

__all__ = ['UtilController']

class UtilController(BaseController):
    
    allow_only = predicates.has_any_permission('manage', 'utilities')
    
    @expose('sapns/util/init.html')
    def init(self):
        return {}
        
    @expose('sapns/util/update.html')
    def update(self):
        return {}
        
    @expose('sapns/util/index.html')
    def index_(self, came_from='/'):
        return dict(page='util', came_from=came_from)

    @expose('sapns/message.html')
    def update_metadata(self, came_from='/dashboard/util'):
        libutil.update_metadata()
        return dict(message=_('Process terminated'), came_from=url(came_from))
    
    @expose(content_type='text/plain')
    def code_model(self, app_name='MyApp', file_name=''):
        mdl = self.extract_model()
        if file_name:
            response.headerlist.append(('Content-Disposition', 
                                        'attachment;filename=%s' % file_name))

        return render_jinja2('sapns/util/model.template',
                             extra_vars=dict(app_name=app_name,
                                             tables=mdl['tables']))
    
    @expose('sapns/util/tables.html')
    def extract_model(self, all_=False):
        return dict(page='extract_model', came_from=url('/dashboard/util'), 
                    tables=libutil.extract_model(all_))
        
    @expose(content_type='text/plain')
    def generate_key(self, fmt=None, n=1):
        """
        IN
          fmt (optional=[8]-[4]-[4]-[4]-[12])
          
          The format of the key to be generated.
          [n] represents a key of length n and we can define a key in different
          parts like this:
          [4]-[2]-[8] would produce a key like this xxxx-xx-xxxxxxxx
          
          Anything outside [n] is taken literally, so we can use different characters
          for our key.
          [5]#[5]![2] would produce a key like this xxxxx#xxxxx!xx
          
          The key characters are: A-Z, a-z, 0-9
          
          n <int> (optional=1)
          The number of keys to be generated
          
        OUT
          The generated key following the corresponding format (fmt).
        """
        
        import random
        random.seed()
        
        def _generate_key(l):
            """generate a l-length key"""
            pop = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
            r = ''
            for _i in xrange(l):
                r += random.choice(pop)
                
            return r
        
        if not fmt:
            fmt = '[8]-[4]-[4]-[4]-[12]'
            
        # substitution function
        def sub_f(m):
            """generate a n-length key for a [n] text"""
            l = int(m.group(1))
            return _generate_key(l)
            
        # generate n keys with the same "fmt" format
        r = []
        for _i in xrange(int(n)):
            # replace every [n] with the corresponding n-length key
            r.append(re.sub(r'\[(\d+)\]', sub_f, fmt))
            
        return '\n'.join(r)