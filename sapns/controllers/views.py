# -*- coding: utf-8 -*-

"""Views management controller"""

from bson.objectid import ObjectId
from neptuno.postgres.search import Search
from neptuno.util import get_paramw
from pylons.i18n import ugettext as _
from sapns.lib.base import BaseController
from sapns.lib.sapns.mongo import Mongo
from sapns.lib.sapns.users import get_user
from sapns.lib.sapns.util import get_template, pagination
from sapns.lib.sapns.views import get_query, COLLECTION_CHAR
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsAttribute, SapnsClass, SapnsPermission
from sqlalchemy.sql.expression import and_
from tg import expose, redirect, url, predicates as p_, config
import copy
import datetime as dt
import hashlib
import logging
import random
import re
import simplejson as sj
import transaction

__all__ = ['ViewsController']

REL_CLASS = 'class'
REL_COLLECTION = 'collection'

class EViews(Exception):
    pass

class ViewsController(BaseController):
    
    allow_only = p_.Any(p_.in_group('managers'),
                        p_.has_permission('views'),
                        )
    
#    @expose('sapns/views/index.html')
#    def index(self, came_from='/'):
#        return dict(page='views', came_from=url(came_from))
    
    @expose('sapns/views/edit/edit.html')
    def edit(self, id_=None, **kw):
        
        _logger = logging.getLogger('ViewsController.edit')
        
        mdb = Mongo().db
        if id_:
            query = ''
            view_ = dbs.query(SapnsClass).get(id_)
            if not view_.view_id:
                view_id = mdb.user_views.insert(dict(creation_date=dt.datetime.now(),
                                                     saved=False,
                                                     attributes=[],
                                                     attributes_detail=[],
                                                     ))
                
            else:
                view_id = view_.view_id
                view0 = mdb.user_views.find_one(dict(_id=ObjectId(view_id)))
                view_copy = copy.deepcopy(view0)
                del view_copy['_id']
                view_id = mdb.user_views.insert(view_copy)
                query = view_copy.get('query', '')
                
            view = dict(id=id_ or '',
                        view_id=str(view_id),
                        title=view_.title,
                        class_id=view_.parent_class_id or view_.class_id,
                        name='%s%s' % (config.get('views_prefix', '_view_'), view_.name),
                        query=query,
                        )
            
        else:
            view_id = mdb.user_views.insert(dict(creation_date=dt.datetime.now(),
                                                 saved=False,
                                                 attributes=[],
                                                 attributes_detail=[],
                                                 ))
            
            view = dict(id=id_ or '',
                        view_id=str(view_id))
            
        user = get_user()
        return dict(page='Edit view', came_from=kw.get('came_from', url(user.entry_point())), 
                    view=view)
    
    @expose()
    def create(self, id_=None, **kw):
        redirect(url('/dashboard/views/edit/'), **kw)
        
    @expose('json')
    def delete(self, **kw):
        logger = logging.getLogger('ViewsController.remove')
        try:
            view_id = get_paramw(kw, 'view_id', str)
            view_name = get_paramw(kw, 'view_name', str, opcional=True)
            
            if view_name:
                self.drop_view(view_name)
            
            mdb = Mongo().db
            mdb.user_views.remove(dict(_id=ObjectId(view_id)))
            
            return dict(status=True)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)
    
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
            
            def _classes(class_id):
                classes = []
                for r_attr in dbs.query(SapnsAttribute).\
                        filter(and_(SapnsAttribute.class_id == class_id,
                                    SapnsAttribute.related_class_id != None,
                                    )):
                    
                    classes.append(dict(data=u'%s (%s)' % (r_attr.related_class.title, r_attr.title),
                                        attr=dict(class_id=r_attr.related_class_id,
                                                  path='%s#%d' % (path, r_attr.attribute_id),
                                                  rel=REL_CLASS,
                                                  ),
                                        state='closed',
                                        children=[],
                                        ))
                    
                # collections
                for r_attr in dbs.query(SapnsAttribute).\
                        filter(and_(SapnsAttribute.related_class_id == class_id)):
                    
                    classes.append(dict(data=r_attr.class_.title,
                                        attr=dict(class_id=r_attr.class_id,
                                                  path='%s#%s%d' % (path, COLLECTION_CHAR, r_attr.attribute_id),
                                                  rel=REL_COLLECTION,
                                                  ),
                                        state='closed',
                                        children=[],
                                        ))

                return sorted(classes, cmp=lambda x,y: cmp(x['data'], y['data']))
            
            if class_id0:
                class0 = dbs.query(SapnsClass).get(class_id0)
                classes = dict(data=class0.title,
                               attr=dict(class_id=class_id0,
                                         path='',
                                         rel=REL_CLASS,
                                         ),
                               state='open',
                               children=_classes(class_id0)
                               )
                
            else:
                classes = _classes(class_id)
                
            return sj.dumps(classes)
            
        except Exception, e:
            logger.error(e)
            return sj.dumps([])        
    
    @expose('json')
    def attributes_list(self, **kw):
        logger = logging.getLogger('ViewsController.attributes_list')
        try:
            class_id = get_paramw(kw, 'class_id', int)
            path_ = get_paramw(kw, 'path', str)
            rel = get_paramw(kw, 'rel', str, opcional=True, por_defecto=REL_CLASS)

            attributes = []
            for attr in dbs.query(SapnsAttribute).\
                    filter(and_(SapnsAttribute.class_id == class_id)).\
                    order_by(SapnsAttribute.title):

                path = '%s#%d' % (path_, attr.attribute_id)
                if rel == REL_COLLECTION:
                    path = '%s#%s%d' % (path_, COLLECTION_CHAR, attr.attribute_id)
                
                attributes.append(dict(id=attr.attribute_id,
                                       title=attr.title,
                                       name=attr.name,
                                       related_class=attr.related_class_id,
                                       path=path,
                                       ))
                
            attr_tmpl = get_template('sapns/views/edit/attribute-list.html')
            
            return dict(status=True, attributes=attr_tmpl.render(attributes=attributes))
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)
        
    def drop_view(self, view_name):
        logger = logging.getLogger('ViewsController.drop_view')
        
        def _exists_view(name):
            e = dbs.execute("SELECT count(*) FROM pg_views WHERE viewname = '%s' " % name).fetchone()
            return e[0] == 1
        
        try:
            # drop "old" view
            if _exists_view(view_name):
                logger.info(u'Dropping "old" view [%s]' % view_name)
                dbs.execute('DROP VIEW %s' % view_name)
                dbs.flush()
                
                c = SapnsClass.by_name('sp_classes')
                c.class_id = c.class_id
                dbs.add(c)
                dbs.flush()
            
        except Exception, e:
            logger.error(e)

    def create_view(self, view_id, view_name, new_name=None, old_name=None):
        
        _logger = logging.getLogger('ViewsController.create_view')
        
        if view_name:
            self.drop_view(view_name)
                
        if old_name:
            self.drop_view(old_name)
                        
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
            self.drop_view(new_name)
            
        query = get_query(view_id)
        dbs.execute('CREATE VIEW %s AS %s' % (view_name, query))
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
                logger.info(prefix)
                for i, attribute_id in enumerate(paths):
                
                    #attribute_id = int(attribute_id.replace(COLLECTION_CHAR, ''))
                    if attribute_id.startswith(COLLECTION_CHAR):
                        attr = dbs.query(SapnsAttribute).get(int(attribute_id.replace(COLLECTION_CHAR, '')))
                        
                        if attr.class_id and i < len(paths)-1:
                            title.append(attr.class_.title)
                            
                        else:
                            title.append(attr.title)
                            
                        # base class
                        if i == 0:
                            base_class = attr.related_class.name
                    
                    else:
                        attr = dbs.query(SapnsAttribute).get(int(attribute_id))
                        
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
                                 width=150,
                                 )
                
                logger.info(attribute)
                
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
        transaction.begin()
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
                        view.parent_class_id = get_paramw(kw, 'class_id', int)
                    
                else:
                    view = SapnsClass()
                    view.parent_class_id = get_paramw(kw, 'class_id', int)
                
            else:
                view = dbs.query(SapnsClass).get(id_)
                
            if view.parent_class_id:
                view.parent_class_id = get_paramw(kw, 'class_id', int)
                
            view.title = title
            view.name = name
            #view.description = u'User view'
            view_id = get_paramw(kw, 'view_id', str)
            view.view_id = view_id
            
            dbs.add(view)
            dbs.flush()
            
            # Look for "list" permission for this class/view
            list_p = dbs.query(SapnsPermission).\
                filter(and_(SapnsPermission.type == SapnsPermission.TYPE_LIST,
                            SapnsPermission.class_id == view.class_id 
                            )).\
                first()
                
            if not list_p:
                # create "list" permission
                list_p = SapnsPermission()
                list_p.permission_name = u'%s#list' % view.name
                list_p.display_name = u'List'
                list_p.class_id = view.class_id
                list_p.type = SapnsPermission.TYPE_LIST
                list_p.requires_id = False
                dbs.add(list_p)
                dbs.flush()
            
            mdb = Mongo().db
            mdb.user_views.update(dict(_id=ObjectId(view_id)),
                                  {'$set': dict(query=kw.get('query', ''), saved=True)})
            
            self.create_view(view_id, get_paramw(kw, 'view_name', str, opcional=True),
                             new_name=view.name, 
                             old_name=get_paramw(kw, 'name', str, opcional=True))
            
            transaction.commit()
            
            return dict(status=True)
        
        except Exception, e:
            transaction.abort()
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
                
            #logger.info(view['attributes_detail'])
            
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
        
    @expose('sapns/views/copy_view/copy_view.html')
    def copy(self, **kw):
        id_class = get_paramw(kw, 'id_class', int)
        cls = dbs.query(SapnsClass).get(id_class)
        
        return dict(cls=dict(id=id_class,
                             name=u'%s (2)' % cls.title,
                             ))
    
    @expose('json')
    def copy_(self, **kw):
        logger = logging.getLogger('ViewsController.copy_view_')
        try:
            id_class = get_paramw(kw, 'id_class', int)
            view_name = get_paramw(kw, 'view_name', unicode)
            
            cls = dbs.query(SapnsClass).get(id_class)
            if cls.view_id is None:
                raise EViews(_(u'There is not a defined view').encode('utf-8'))
            
            name = re.sub(r'[^a-z0-9_]', '_', view_name.lower())
            if SapnsClass.by_name(name):
                raise EViews(_(u'A class with the same name already exists').encode('utf-8'))
            
            # create "class"
            cls_c = SapnsClass()
            cls_c.title = view_name
            cls_c.name = name
            cls_c.parent_class_id = cls.parent_class_id
            
            # copy "view"
            mdb = Mongo().db
            
            view0 = mdb.user_views.find_one(dict(_id=ObjectId(cls.view_id)))
            view_copy = copy.deepcopy(view0)
            del view_copy['_id']
            view_id = mdb.user_views.insert(view_copy)
            cls_c.view_id = str(view_id)
            
            dbs.add(cls_c)
            dbs.flush()
            
            # create "list" permission
            list_p = SapnsPermission()
            list_p.permission_name = u'%s#list' % cls_c.name
            list_p.display_name = u'List'
            list_p.class_id = cls_c.class_id
            list_p.type = SapnsPermission.TYPE_LIST
            list_p.requires_id = False
            dbs.add(list_p)
            dbs.flush()
            
            self.create_view(view_id, '', new_name=cls_c.name)            
            
            return dict(status=True)
            
        except EViews, e:
            logger.error(e)
            return dict(status=False, msg=str(e))
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)