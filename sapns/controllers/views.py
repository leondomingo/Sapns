# -*- coding: utf-8 -*-
"""Views management controller"""

# turbogears imports
import simplejson as sj
from tg import expose, validate, redirect, url

# third party imports
#from pylons.i18n import ugettext as _
#from repoze.what import predicates

# project specific imports
from sapns.lib.base import BaseController
from formencode import schema, validators
from pylons import tmpl_context
#from sapns.model import DBSession, metadata

class ViewSchema(schema.Schema):
    pass   

class ViewsController(BaseController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = authorize.not_anonymous()
    
    @expose('views/view.html')
    def edit(self, id=None):
        
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
                
        return dict(page='views/edit', view=view)

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
    
    @expose('json')
    @validate(validators={'title': validators.NotEmpty(), 'code': validators.NotEmpty()}, 
              error_handler=error_handler)
    def save(self, **kw):
        
        id = validators.Int().to_python(kw['id'])
        
        redirect(url('/views/edit'))