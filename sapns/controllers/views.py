# -*- coding: utf-8 -*-
"""Views management controller"""

from neptuno.util import get_paramw
from pylons.i18n import ugettext as _
from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsAttribute, SapnsClass
from tg import expose, redirect, url, predicates
import logging
import simplejson as sj
from sqlalchemy.sql.expression import and_
from sapns.lib.sapns.util import get_template
import re

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
    def classes(self, **kw):
        logger = logging.getLogger('ViewsController.classes')
        try:
            class_id = get_paramw(kw, 'class_id', int, opcional=True)
            class_id0 = None
            path = ''
            if not class_id:
                class_id = class_id0 = get_paramw(kw, 'class_id0', int)
                
            else:
                path = get_paramw(kw, 'path', str)
            
            def _has_children(class_id):
                return dbs.query(SapnsAttribute).\
                    filter(SapnsAttribute.related_class_id == class_id).\
                    first() != None
            
            def _state(class_id):
                state_ = ''
                if _has_children(class_id):
                    state_ = 'closed'
                        
                return state_
            
            def _classes(class_id):
                classes = []
                for r_attr in dbs.query(SapnsAttribute).\
                        filter(and_(SapnsAttribute.class_id == class_id,
                                    SapnsAttribute.related_class_id != None,
                                    )):
                    
                    classes.append(dict(data=u'%s (%s)' % (r_attr.related_class.title, r_attr.title),
                                        attr=dict(class_id=r_attr.related_class_id,
                                                  path='%d#%s' % (r_attr.attribute_id, path),
                                                  rel='class',
                                                  ),
                                        state=_state(r_attr.class_id),
                                        children=[],
                                        ))
                    
                return classes
            
            if class_id0:
                class0 = dbs.query(SapnsClass).get(class_id0)
                classes = dict(data=class0.title,
                               attr=dict(class_id=class_id0,
                                         path='',
                                         rel='class',
                                         ),
                               state='open',
                               children=_classes(class_id0)
                               )
                
            else:
                classes = _classes(class_id)
                
            return sj.dumps(classes)
            
#            id_departamento_ = get_paramw(kw, 'id_departamento', int, opcional=True)
#            if not id_producto and not id_curso and not id_departamento_:
#                
#                # productos "raíz"
#                if id_departamento:
#                    # con departamento seleccionado
#                    dpto = dbs.query(Departamentos).get(id_departamento)
#                    productos=dict(data=dpto.nombre,
#                                   attr=dict(id_departamento=dpto.id_,
#                                             rel='departamento',
#                                             id='departamento_%d' % dpto.id_),
#                                   state='open',
#                                   children=_productos(id_departamento, None)
#                                   )
#                    
#                else:
#                    # sin departamento seleccionado
#                    productos = []
#                    # sólo los departamentos del usuario
#                    departamentos = get_departamentos()
#                    for dpto in departamentos:
#                        productos.append(dict(data=dpto['nombre'],
#                                              attr=dict(id_departamento=dpto['id'],
#                                                        rel='departamento',
#                                                        id='departamento_%d' % dpto['id']),
#                                              state='closed',
#                                              children=_productos(dpto['id'], None)
#                                              ))
#
#            elif id_producto:
#                # productos "hijo" de id_producto
#                productos = _productos(id_departamento, id_producto)
#                
#                if len(productos) == 0:
#                    productos = _cursos(id_producto)
#    
#            return sj.dumps(productos)
        
        except Exception, e:
            logger.error(e)
            return sj.dumps([])        
    
    @expose('json')
    def attributes_list(self, **kw):
        logger = logging.getLogger('ViewsController.attributes_list')
        try:
            class_id = get_paramw(kw, 'class_id', int)
            path = get_paramw(kw, 'path', str)
            
            attributes = []
            for attr in dbs.query(SapnsAttribute).\
                    filter(and_(SapnsAttribute.class_id == class_id)).\
                    order_by(SapnsAttribute.title):
                
                #attr = SapnsAttribute()
                attributes.append(dict(id=attr.attribute_id,
                                       title=attr.title,
                                       name=attr.name,
                                       related_class=attr.related_class_id,
                                       path='%d#%s' % (attr.attribute_id, path),
                                       ))
                
            attr_tmpl = get_template('sapns/views/edit/attribute-list.html')
            
            return dict(status=True, attributes=attr_tmpl.render(attributes=attributes))
        
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