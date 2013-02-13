# -*- coding: utf-8 -*-
"""Views management controller"""

from neptuno.util import get_paramw
from pylons.i18n import ugettext as _
from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsAttribute
from tg import expose, redirect, url, predicates
import logging
import simplejson as sj
from sqlalchemy.sql.expression import and_

__all__ = ['ViewsController']

class ViewsController(BaseController):
    
    allow_only = predicates.has_any_permission('manage', 'views')
    
    @expose('sapns/views/index.html')
    def index(self, came_from='/'):
        return dict(page='views', came_from=url(came_from))
    
    @expose('sapns/views/edit/edit.html')
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
    
    @expose('json')
    def attributes_list(self, **kw):
        logger = logging.getLogger('ViewsController.attributes_list')
        try:
            class_id = get_paramw(kw, 'class_id', int)
            
            attributes = []
            for attr in dbs.query(SapnsAttribute).\
                    filter(and_(SapnsAttribute.class_id == class_id)).\
                    order_by(SapnsAttribute.title):
                
                attr = SapnsAttribute()
                
                attributes.append(dict(id=attr.attribute_id,
                                       title=attr.title,
                                       name=attr.name,
                                       related_class=attr.related_class_id,
                                       ))
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)

    @expose('sapns/views/view.html')
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
        
    @expose('sapns/views/share.html')
    def share(self, **kw):
        came_from = kw.get('came_from', url('/views'))
        # TODO: views/share
        return dict(page='views/share', came_from=came_from)
    
    @expose('sapns/message.html')
    def delete(self, id_view=None, came_from='/views'):
        
        return dict(message=_('The view has been successfully deleted'),
                    came_from=came_from)