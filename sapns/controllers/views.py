# -*- coding: utf-8 -*-
"""Views management controller"""

from bson.objectid import ObjectId
from neptuno.postgres.search import Search
from neptuno.util import get_paramw
from pylons.i18n import ugettext as _
from sapns.lib.base import BaseController
from sapns.lib.sapns.mongo import Mongo
from sapns.lib.sapns.util import get_template, pagination
from sapns.lib.sapns.views import get_query
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsAttribute, SapnsClass
from sqlalchemy.sql.expression import and_
from tg import expose, redirect, url, predicates as p_, config
import datetime as dt
import hashlib
import logging
import random
import simplejson as sj
import re

__all__ = ['ViewsController']

class ViewsController(BaseController):
    
    allow_only = p_.Any(p_.in_group('managers'),
                        p_.has_permission('views'),
                        )
    
    @expose('sapns/views/index.html')
    def index(self, came_from='/'):
        return dict(page='views', came_from=url(came_from))
    
    @expose('sapns/views/edit/edit.html')
    def edit(self, id_=None, came_from='/'):
        
        if id_:
            view_ = dbs.query(SapnsClass).get(id_)
            
            if not view_.view_id:
                mdb = Mongo().db
                view_id = mdb.user_views.insert(dict(creation_date=dt.datetime.now(),
                                                     saved=False,
                                                     attributes=[],
                                                     attributes_detail=[],
                                                     ))
                
            else:
                view_id = view_.view_id
                
            view = dict(id=id_ or '',
                        view_id=str(view_id),
                        title=view_.title,
                        class_id=view_.parent_class_id or view_.class_id,
                        name='%s%s' % (config.get('views_prefix', '_view_'), view_.name),
                        )
            
        else:
            mdb = Mongo().db
            view_id = mdb.user_views.insert(dict(creation_date=dt.datetime.now(),
                                                 saved=False,
                                                 attributes=[],
                                                 attributes_detail=[],
                                                 ))
            
            view = dict(id=id_ or '',
                        view_id=str(view_id))
                        
        return dict(page='views/edit', came_from=came_from, view=view)
    
    @expose()
    def create(self, id_=None, **kw):
        redirect(url('/dashboard/views/edit/'), **kw)
    
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
            
#            def _has_children(class_id):
#                return dbs.query(SapnsAttribute).\
#                    filter(SapnsAttribute.related_class_id == class_id).\
#                    first() != None
#            
#            def _state(class_id):
#                state_ = ''
#                if _has_children(class_id):
#                    state_ = 'closed'
#
#                return state_
            
            def _classes(class_id):
                classes = []
                for r_attr in dbs.query(SapnsAttribute).\
                        filter(and_(SapnsAttribute.class_id == class_id,
                                    SapnsAttribute.related_class_id != None,
                                    )):
                    
                    classes.append(dict(data=u'%s (%s)' % (r_attr.related_class.title, r_attr.title),
                                        attr=dict(class_id=r_attr.related_class_id,
                                                  path='%s#%d' % (path, r_attr.attribute_id),
                                                  rel='class',
                                                  ),
                                        state='closed', #_state(r_attr.class_id),
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
                                       path='%s#%d' % (path, attr.attribute_id),
                                       ))
                
            attr_tmpl = get_template('sapns/views/edit/attribute-list.html')
            
            return dict(status=True, attributes=attr_tmpl.render(attributes=attributes))
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)

    def create_view(self, view_id, view_name, new_name=None):
        
        logger = logging.getLogger('ViewsController.create_view')
        
        def _exists_view(name):
            e = dbs.execute("SELECT count(*) FROM pg_views WHERE viewname = '%s' " % name).fetchone()
            return e[0] == 1
        
        if view_name:
            try:
                # drop "old" view
                if _exists_view(view_name):
                    logger.info(u'Dropping "old" view [%s]' % view_name)
                    dbs.execute('DROP VIEW %s' % view_name)
                    dbs.flush()
                
            except Exception, e:
                logger.error(e)
                        
        # create a new view
        if not new_name:
            sha1 = hashlib.sha1()
            sha1.update(str(dt.datetime.now()))
            random.seed()
            view_name = '_temp_view_%s_%.6d' % (sha1.hexdigest(), random.randint(0, 999999))
            
        else:
            # "_view_xxx", where xxx=<new_name>
            view_name = '%s%s' % (config.get('views_prefix', '_view_'), new_name)
            
            # TODO: drop view with "new_name"
            try:
                if _exists_view(view_name):
                    logger.info(u'Dropping view "%s"' % view_name)
                    dbs.execute('DROP VIEW %s' % view_name)
                    dbs.flush()
            except Exception, e:
                logger.error(e)
            
        query = get_query(view_id)
        s = 'CREATE VIEW %s AS %s' % (view_name, query)
        #logger.info(s)
        dbs.execute(s)
        dbs.flush()
        
        c = SapnsClass.by_name('sp_classes')
        c.class_id = c.class_id
        dbs.add(c)
        dbs.flush()
        
        return view_name
    
    @expose('sapns/views/edit/cols-list.html')
    def view_cols(self, **kw):
        view_id = get_paramw(kw, 'view_id', str)
        
        mdb = Mongo().db
        view = mdb.user_views.find_one(dict(_id=ObjectId(view_id)))
        
        cols = []
        for attribute in sorted(view['attributes_detail'], cmp=lambda x,y: cmp(x.get('order', 0), y.get('order', 0))):
            cols.append(dict(path=attribute['path'],
                             expression=attribute['expression'],
                             title=attribute['title'],
                             ))
            
        return dict(cols=cols)
        
    @expose('json')
    def add_attribute(self, **kw):
        logger = logging.getLogger('add_attribute')
        try:
            view_id = get_paramw(kw, 'view_id', str)
            
            mdb = Mongo().db
            view = mdb.user_views.find_one(dict(_id=ObjectId(view_id)))
            
            title = []
            base_class = ''
            attribute_path = get_paramw(kw, 'attribute_path', str)
            attribute = {}
            view_name = ''
            if view['attributes'].count(attribute_path) == 0:
                
                paths = attribute_path.split('#')[1:]
                prefix = '_'.join(paths[:-1]) or '0'
                for i, attribute_id in enumerate(paths):
                    attr = dbs.query(SapnsAttribute).get(attribute_id)
                    if attr.related_class_id and i < len(paths)-1:
                        title.append(attr.related_class.title)
                        
                    else:
                        title.append(attr.title)
                        
                    # base class
                    if i == 0:
                        base_class = attr.class_.name 
                        
                attribute = dict(order=len(view['attributes']),
                                 title='.'.join(title),
                                 expression='%s_%s.%s' % (attr.class_.name, prefix, attr.name),
                                 path=attribute_path,
                                 class_name=attr.class_.name,
                                 class_alias='%s_%s' % (attr.class_.name, prefix),
                                 )
                
                mdb.user_views.update(dict(_id=ObjectId(view_id)),
                                      {'$set': dict(base_class=base_class),
                                       '$push': dict(attributes_detail=attribute,
                                                     attributes=attribute_path)
                                       })
                
                view_name = self.create_view(view_id, get_paramw(kw, 'view_name', str, opcional=True))
                
            return dict(status=True, attribute=attribute, view_name=view_name)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)
        
    @expose('json')
    def reorder_attributes(self, **kw):
        logger = logging.getLogger('ViewsController.reorder_attributes')
        try:
            view_name = get_paramw(kw, 'view_name', str, opcional=True)
            
            order = {}
            for k, v in kw.iteritems():
                m = re.search(r'^atr_(\d+)', k)
                if m:
                    order[v] = int(m.group(1))
                    
            mdb = Mongo().db
                    
            view_id = get_paramw(kw, 'view_id', str)
            view = mdb.user_views.find_one(dict(_id=ObjectId(view_id)))
            for attr in view['attributes_detail']:
                attr['order'] = order[attr['path']]
                
            mdb.user_views.update(dict(_id=ObjectId(view_id)),
                                  {'$set': dict(attributes_detail=view['attributes_detail'])})
            
            view_name = self.create_view(view_id, view_name)
            
            return dict(status=True, view_name=view_name)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)
        
    @expose('sapns/views/edit/edit-attribute.html')
    def edit_attribute(self, **kw):
        
        view_id = get_paramw(kw, 'view_id', str)
        path = get_paramw(kw, 'path', str)
        
        mdb = Mongo().db
        view = mdb.user_views.find_one(dict(_id=ObjectId(view_id))) 
        
        for attr in view['attributes_detail']:
            if attr['path'] == path:
                attribute = dict(title=attr['title'],
                                 expression=attr['expression'],
                                 path=attr['path'],
                                 )
                break
        
        return dict(view_id=view_id, view_name=kw.get('view_name', ''), attribute=attribute)
    
    @expose('json')
    def remove_attribute(self, **kw):
        logger = logging.getLogger('ViewsController.remove_attribute')
        try:
            view_id = get_paramw(kw, 'view_id', str)
            path = get_paramw(kw, 'path', unicode)
            
            mdb = Mongo().db
            view = mdb.user_views.find_one(dict(_id=ObjectId(view_id)))
            
            view['attributes'].remove(path)
            attributes_detail = []
            for attr in view['attributes_detail']:
                if attr['path'] != path:
                    attributes_detail.append(attr)
                
            mdb.user_views.update(dict(_id=ObjectId(view_id)),
                                  {'$set': dict(attributes=view['attributes'],
                                                attributes_detail=attributes_detail)})
            
            view_name = self.create_view(view_id, get_paramw(kw, 'view_name', str, opcional=True))
            
            return dict(status=True, view_name=view_name)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)
        
    @expose('json')
    def view_save(self, **kw):
        logger = logging.getLogger('ViewsController.view_save')
        try:
            title = get_paramw(kw, 'title', unicode)
            name = re.sub(r'[^a-z0-9_]', '_', title.lower())
            
            user_id = get_paramw(kw, 'user_id', int, opcional=True)
            if user_id:
                name = '%s_%d' % (name, user_id)
            
            id_ = get_paramw(kw, 'id', int, opcional=True)
            if not id_:
                if name:
                    class_ = SapnsClass.by_name(name.decode('utf-8'))
                    if class_:
                        view = class_
                        
                    else:
                        view = SapnsClass()
                    
                else:
                    view = SapnsClass()
                
            else:
                view = dbs.query(SapnsClass).get(id_)
                
            view.title = title
            view.name = name
            view.parent_class_id = get_paramw(kw, 'class_id', int)
            #view.description = u'User view'
            view_id = get_paramw(kw, 'view_id', str)
            view.view_id = view_id
            
            dbs.add(view)
            dbs.flush()
            
            self.create_view(view_id, get_paramw(kw, 'view_name', str, opcional=True),
                             new_name=view.name)
            
            return dict(status=True)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)            
    
    @expose('json')
    def attribute_save(self, **kw):
        logger = logging.getLogger('ViewsController.attribute_save')
        try:
            view_id = get_paramw(kw, 'view_id', str)
            path = get_paramw(kw, 'path', unicode)
            
            mdb = Mongo().db
            view = mdb.user_views.find_one(dict(_id=ObjectId(view_id)))
            
            for i, attr in enumerate(view['attributes_detail']):
                if attr['path'] == path:
                    logger.info(attr)
                    view['attributes_detail'][i]['title'] = get_paramw(kw, 'title', unicode)
                    view['attributes_detail'][i]['expression'] = get_paramw(kw, 'expression', unicode)
                    break
                
            logger.info(view['attributes_detail'])
            
            mdb.user_views.update(dict(_id=ObjectId(view_id)),
                                  {'$set': dict(attributes_detail=view['attributes_detail'])})
            
            view_name = self.create_view(view_id, get_paramw(kw, 'view_name', str, opcional=True))
            
            return dict(status=True, view_name=view_name)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)
    
    @expose('json')
    def grid(self, **kw):
        """
        OUT
          {
           status: <bool>,
           cols: [{title: <str>, width: <int>, align: <str>}, ...],
           data: [[<unicode>, ...], [<unicode>, ...], ...],
           styles: [<str>, ...],
           this_page: <int>,
           total_count: <int>,
           total_pag: <int>
          }
        """
        
        cls = get_paramw(kw, 'cls', unicode)
        q = get_paramw(kw, 'q', unicode, opcional=True, por_defecto='')
        rp = get_paramw(kw, 'rp', int, opcional=True, por_defecto=10)
        pag_n = get_paramw(kw, 'pag_n', int, opcional=True, por_defecto=1)
        
        pos = (pag_n-1) * rp
        
        # get dataset
        _search = Search(dbs, cls) #, strtodatef=_strtodate)
        _search.apply_qry(q.encode('utf-8'))
        
        ds = _search(rp=rp, offset=pos, no_count=True)
        
        # Reading global settings
        ds.date_fmt = config.get('formats.date', default='%m/%d/%Y')
        ds.time_fmt = config.get('formats.time', default='%H:%M')
        ds.datetime_fmt = config.get('formats.datetime', default='%m/%d/%Y %H:%M')
        ds.true_const = _('Yes')
        ds.false_const = _('No')
        
        #ds.float_fmt = app_cfg.format_float
        
        visible_width = 800
        min_width = visible_width / 6
        
        default_width = visible_width / len(ds.labels)
        if default_width < min_width:
            default_width = min_width
        
        cols = []
        for col in ds.labels:
            w = default_width
            if col == 'id':
                w = 60
                
            cols.append(dict(title=col, width=w, align='center'))
            
        this_page, total_pag = pagination(rp, pag_n, ds.count)
        
        if ds.count == rp:
            total_pag = pag_n + 1
        
        return dict(status=True, cols=cols, data=ds.to_data(), styles=[],
                    this_page=this_page, total_count=ds.count, total_pag=total_pag)    

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