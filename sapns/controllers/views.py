# -*- coding: utf-8 -*-
"""Views management controller"""

# turbogears imports
import simplejson as sj
from tg import expose, redirect, url

# third party imports
from pylons.i18n import ugettext as _
from repoze.what import authorize

# project specific imports
from sapns.lib.base import BaseController
from formencode import schema #, validators
#from pylons import tmpl_context
#from sapns.model import DBSession, metadata

__all__ = ['ViewsController']

class ViewSchema(schema.Schema):
    pass   

class ViewsController(BaseController):
    
    allow_only = authorize.has_any_permission('manage', 'views')
    
    @expose('views/index.html')
    def index(self, came_from='/'):
        return dict(page='views', came_from=url(came_from))
    
    @expose('views/view.html')
    def edit(self, id=None, came_from='/'):
        
        # TODO: cargar datos de la vista con ese "id"
        #id = validators.Int().to_python(id)
        
        # fake data
        columns = [dict(title='t1',
                        definition='d1',
                        alias='a1',
                        align='right',
                        ),
                   dict(title='t2',
                        definition='d2',
                        alias='a2',
                        align='left',
                        ),
                   ]
        
        relations = [dict(table='alumnos',
                          alias='alum',
                          condition='',
                          ),
                     dict(table='clientes',
                          alias='clie_a',
                          condition='clie_a.id = alum.id_clientes_clienteactual'
                          ) 
                    ]
        filters = ['f1', 'f2', 'f3']
        order = ['o1', 'o2', 'o3']
        
        view = dict(id=id or '',
                    title=u'Title',
                    code=u'Code',
                    columns=columns,
                    relations=relations,
                    filters=filters,
                    order=order)
                
        return dict(page='views/edit', came_from=came_from, view=view)

    @expose('views/view.html')
    def error_handler(self, **kw):
        view = dict(id=kw['id'],
                    title=kw['title'],
                    code=kw['code'],
                    columns=sj.loads(kw['columns']),
                    relations=sj.loads(kw['relations']),
                    filters=sj.loads(kw['filters']),
                    order=sj.loads(kw['order']),
                    )
        
        return dict(page='views/edit', view=view)
    
    @expose() #'json')
#    @validate(validators={'title': validators.NotEmpty(), 'code': validators.NotEmpty()}, 
#              error_handler=error_handler)
    def save(self, **kw):
        #id = validators.Int().to_python(kw['id'])
        redirect(url('/views/edit'))
        
    @expose('views/share.html')
    def share(self, **kw):
        came_from = kw.get('came_from', url('/views'))
        # TODO: views/share
        return dict(page='views/share', came_from=came_from)
    
    @expose('message.html')
    def delete(self, id_view=None, came_from='/views'):
        
        return dict(message=_('The view has been successfully deleted'),
                    came_from=came_from)