# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs
from pylons.i18n import ugettext as _
# more imports here...
from pylons.templating import render_jinja2

class Update(object):

    def render(self, template, extra_vars):
        return render_jinja2(template, extra_vars=extra_vars)
    
    def __call__(self):
        print _('Ok')
        print render_jinja2('sapns/init/sp_users.view.sql', {})
    
update = Update()