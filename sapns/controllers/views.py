# -*- coding: utf-8 -*-
"""Views management controller"""

# turbogears imports
from tg import expose
#from tg import redirect, validate, flash

# third party imports
#from pylons.i18n import ugettext as _
#from repoze.what import predicates

# project specific imports
from sapns.lib.base import BaseController
#from sapns.model import DBSession, metadata


class ViewsController(BaseController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = authorize.not_anonymous()
    
    @expose('views/view.html')
    def edit(self, id=None):
        filters = ['f1', 'f2', 'f3']
        order = ['o1', 'o2', 'o3']
        
        return dict(page='views/edit', 
                    view=dict(title=u'Title',
                              code=u'Code',
                              columns=[],
                              relations=[dict(table='alumnos',
                                              alias='alum',
                                              condition='',
                                              )],                              
                              filters=filters,
                              order=order))

