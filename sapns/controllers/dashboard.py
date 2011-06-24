# -*- coding: utf-8 -*-
"""Dashboard Controller"""

from tg import response, expose, require, url, request, redirect, config
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tg.i18n import set_lang, get_lang
from repoze.what import predicates

from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs
import sapns.config.app_cfg as app_cfg

from neptuno.postgres.search import search
from neptuno.util import strtobool, strtodate, strtotime, datetostr

from tg.controllers.util import urlencode
from sapns.model.sapnsmodel import SapnsUser, SapnsShortcut, SapnsClass,\
    SapnsPrivilege, SapnsAttribute, SapnsAttrPrivilege, SapnsAction

import logging
import re
import simplejson as sj
import cStringIO
from sqlalchemy import Table
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.schema import MetaData
from sqlalchemy.sql.expression import and_
from sapns.controllers.views import ViewsController
from sapns.controllers.util import UtilController
from sapns.controllers.users import UsersController
from sapns.controllers.shortcuts import ShortcutsController
from sapns.controllers.messages import MessagesController

__all__ = ['DashboardController']

class DashboardController(BaseController):
    """DashboardController manage raw-data editing"""
    
    views = ViewsController()
    util = UtilController()
    users = UsersController()
    sc = ShortcutsController()
    messages = MessagesController()

    @expose('sapns/dashboard/index.html')
    @require(predicates.not_anonymous())
    def index(self, sc_type='list', sc_parent=None):
        curr_lang = get_lang()

        # connected user
        user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
        
        # get children shortcuts (shortcuts.parent_id = sc_parent) of the this user
        shortcuts = user.get_shortcuts(id_parent=sc_parent)
        
        if sc_parent:
            sc_parent = dbs.query(SapnsShortcut).get(sc_parent).parent_id
            
        else:
            sc_parent = None
            
        # number of messages
        messages = user.messages()
        unread = user.unread_messages()
        
        return dict(page='dashboard', curr_lang=curr_lang, shortcuts=shortcuts,
                    messages=messages, unread=unread, 
                    sc_type=sc_type, sc_parent=sc_parent)
        
    @expose()
    def init(self):
        redirect(url('/dashboard/util/init'))

    @expose('sapns/dashboard/listof.html')
    @require(predicates.not_anonymous())
    def list(self, cls, q='', **params):
        
        logger = logging.getLogger(__name__ + '/list')
        logger.info('params=%s' % params)

        # picking up parameters
        rp = params.get('rp', 10)
        pag_n = params.get('pag_n', 1)
        caption = params.get('caption', '')
        show_ids = params.get('show_ids', 'false')
        
        came_from = params.get('came_from', '')
        if came_from:
            came_from = url(came_from)
            
        # collections
        ch_attr = params.get('ch_attr')
        parent_id = params.get('parent_id')
        
        # does this user have permission on this table?
        user = dbs.query(SapnsUser).get(int(request.identity['user'].user_id))
        
        if not user.has_privilege(cls):
            redirect(url('/message', 
                         params=dict(message=_('Sorry, you do not have privilege on this class'),
                                     came_from=came_from)))
        
        rp = int(rp)
        pag_n = int(pag_n)
        show_ids = strtobool(show_ids)
        
        pos = (pag_n-1) * rp

        meta = MetaData(bind=dbs.bind)
        
        # views prefix
        prefix = config.get('views_prefix', '_view_')
            
        # user's view
        try:
            view_name = '%s%s_%d' % (prefix, cls, user.user_id)
            Table(view_name, meta, autoload=True)
            view = view_name
        
        except NoSuchTableError:
            # general view
            try:
                view_name = '%s%s' % (prefix, cls)
                Table(view_name, meta, autoload=True)
                view = view_name
        
            except NoSuchTableError:
                # "raw" table
                view = cls
            
        date_fmt = config.get('grid.date_format', default='%m/%d/%Y')
        
        def strtodatef(s):
            return strtodate(s, fmt=date_fmt, no_exc=True)
        
        logger.info('search...%s / q=%s' % (view, q))
        
        cls_ = SapnsClass.by_name(cls)
        
        # related classes
        rel_classes = cls_.related_classes()
        
        # collection
        col = None
        if ch_attr and parent_id:
            col = (cls, ch_attr, parent_id,)
            
            p_cls = cls_.attr_by_name(ch_attr).related_class
            p_title = SapnsClass.object_title(p_cls.name, parent_id)
            
            caption = _('%s of [%s]' % (cls_.title, p_title))
            
        # get dataset
        ds = search(dbs, view, q=q.encode('utf-8'), rp=rp, offset=pos, 
                    show_ids=show_ids, strtodatef=strtodatef, collection=col) 
        
        # Reading global settings
        ds.date_fmt = date_fmt
        ds.time_fmt = config.get('grid.time_format', default='%H:%M')
        ds.datetime_fmt = config.get('grid.datetime_format', default='%m/%d/%Y %H:%M')
        ds.true_const = config.get('grid.true_const', default='Yes')
        ds.false_const = config.get('grid.false_const', default='No')
        
        ds.float_fmt = app_cfg.format_float
        
        data = ds.to_data()
        
        cols = []
        for col in ds.labels:
            w = 125
            if col == 'id':
                w = 60
                
            cols.append(dict(title=col,
                             width=w,
                             align='center'))
        
        # actions for this class
        actions = cls_.sorted_actions()
        actions = [act for act in actions \
                   if act['type'] in [SapnsAction.TYPE_NEW,
                                      SapnsAction.TYPE_EDIT,
                                      SapnsAction.TYPE_DELETE,
                                      SapnsAction.TYPE_PROCESS,
                                     ]]

        # total number of pages
        total_pag = 1
        if rp > 0:
            total_pag = ds.count/rp
            
            if ds.count % rp != 0:
                total_pag += 1
            
            if total_pag == 0:
                total_pag = 1
        
        # rows in this page
        totalp = ds.count - pos
        if rp and totalp > rp:
            totalp = rp
            
        link_data = dict(q=q, rp=rp, pag_n=pag_n, caption=caption, 
                         show_ids=show_ids)
        
        if ch_attr and parent_id:
            link_data['ch_attr'] = ch_attr
            link_data['parent_id'] = parent_id
            
        return dict(page='list',
                    q=q, show_ids=show_ids, came_from=came_from,
                    # collection
                    ch_attr=ch_attr, parent_id=parent_id,
                    # related classes
                    rel_classes=rel_classes,
                    link=('/dashboard/list/%s/?' % cls) + urlencode(link_data),
                    grid=dict(caption=caption, name=cls, cls=cls,
                              search_url=url('/dashboard/list/'), 
                              cols=cols, data=data, 
                              actions=actions, pag_n=pag_n, rp=rp, pos=pos,
                              totalp=totalp, total=ds.count, total_pag=total_pag))
    
    @expose('sapns/dashboard/search.html')
    @require(predicates.not_anonymous())
    def search(self, **params):
        logger = logging.getLogger(__name__ + '/search')
        logger.info(params)
        
        return self.list(**params)
    
    def export(self, cls, **kw):
        """
        IN
          cls          <unicode>
          kw
            q          <unicode>
            ch_attr    <unicode>
            parent_id  <int>
        """
        
        meta = MetaData(bind=dbs.bind)
        
        # parameters
        # q
        q = kw.get('q', '')
        
        # user
        user = dbs.query(SapnsUser).get(int(request.identity['user'].user_id))
        
        # collections
        ch_attr = kw.get('ch_attr')
        parent_id = kw.get('parent_id')
        
        # collection
        col = None
        if ch_attr and parent_id:
            col = (cls, ch_attr, parent_id,)
            
                # views prefix
        prefix = config.get('views_prefix', '_view_')

        # user's view
        try:
            view_name = '%s%s_%d' % (prefix, cls, user.user_id)
            Table(view_name, meta, autoload=True)
            view = view_name
        
        except NoSuchTableError:
            # general view
            try:
                view_name = '%s%s' % (prefix, cls)
                Table(view_name, meta, autoload=True)
                view = view_name
        
            except NoSuchTableError:
                # "raw" table
                view = cls
        
        date_fmt = config.get('grid.date_format', default='%m/%d/%Y')
        
        def strtodatef(s):
            return strtodate(s, fmt=date_fmt, no_exc=True)
        
        # get dataset
        ds = search(dbs, view, q=q.encode('utf-8'), rp=0, collection=col)
        
        return ds 
    
    @expose(content_type='text/csv')
    @require(predicates.not_anonymous())
    def tocsv(self, cls, **kw):
        ds = self.export(cls, **kw)
        
        response.headerlist.append(('Content-Disposition',
                                    'attachment;filename=%s.csv' % cls.encode('utf-8')))
        
        return ds.to_csv()
    
    @expose(content_type='application/excel')
    @require(predicates.not_anonymous())
    def toxls(self, cls, **kw):
        ds = self.export(cls, **kw)

        response.headerlist.append(('Content-Disposition',
                                    'attachment;filename=%s.xls' % cls.encode('utf-8')))
        
        # generate XLS content into "memory file"
        xl_file = cStringIO.StringIO()
        ds.to_xls(cls.capitalize().replace('_', ' '), xl_file)
        
        return xl_file.getvalue()
    
    @expose('json')
    @require(predicates.not_anonymous())
    def title(self, cls, id):
        logger = logging.getLogger(__name__ + '/title')
        try:
            title = SapnsClass.object_title(cls, id)
            return dict(status=True, title=title)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e))        
    
    @expose()
    @require(predicates.not_anonymous())
    def save(self, cls, id='', **params):
        """
        IN
          cls          <unicode>
          id           <int>
          params
            came_from  <unicode>
            fld_*      ???        Fields to be saved
        """
        
        logger = logging.getLogger(__name__ + '/save')
        logger.info(params)

        cls = SapnsClass.by_name(cls)
        came_from = params.get('came_from') #, '/dashboard/list?cls=%s' % cls.name)
        quiet = strtobool(params.get('quiet', 'false'))
        
        # does this user have permission on this table?
        user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
        
        if not user.has_privilege(cls.name):
            redirect(url('/message', 
                         params=dict(message=_('Sorry, you do not have privilege on this class'),
                                     came_from=came_from)))

        # init "update" dictionary
        update = {}
        
        if id:
            update['id'] = int(id)
            
        READONLY_DENIED = [SapnsAttrPrivilege.ACCESS_READONLY, 
                           SapnsAttrPrivilege.ACCESS_DENIED]
        
        for field_name, field_value in params.iteritems():
            m_field = re.search(r'^fld_(.+)', field_name)
            if m_field:
                field_name_ = m_field.group(1) 
                attr = cls.attr_by_name(field_name_)
                
                # skipping "read-only" and "denied" attributes
                acc = SapnsAttrPrivilege.get_access(user.user_id, attr.attribute_id)
                if acc in READONLY_DENIED:
                    continue
                
                # null values
                if field_value == 'null':
                    field_value = None
                    
                else:
                    # integer
                    if attr.type == SapnsAttribute.TYPE_INTEGER:
                        if field_value == '':
                            field_value = None
                        else:
                            field_value = int(field_value)
                    
                    # numeric
                    elif attr.type == SapnsAttribute.TYPE_FLOAT:
                        if field_value == '':
                            field_value = None
                        else:
                            field_value = float(field_value)
                    
                    # boolean
                    elif attr.type == SapnsAttribute.TYPE_BOOLEAN:
                        field_value = strtobool(field_value)
                        
                    # date
                    elif attr.type == SapnsAttribute.TYPE_DATE:
                        if field_value == '':
                            field_value = None
                        else:
                            field_value = strtodate(field_value, fmt='%Y-%m-%d')
                    
                    # time
                    elif attr.type == SapnsAttribute.TYPE_TIME:
                        if field_value == '':
                            field_value = None
                        else:
                            field_value = strtotime(field_value)
                    
                    # string types        
                    else:
                        field_value = field_value.strip()
                
                update[field_name_] = field_value
                
        logger.info(update)
                
        meta = MetaData(bind=dbs.bind)
        tbl = Table(cls.name, meta, autoload=True)
        
        if update.get('id'):
            logger.info('Updating object [%d] of "%s"' % (update['id'], cls.name))
            tbl.update(whereclause=tbl.c.id == update['id'], values=update).execute()
            
        else:
            logger.info('Inserting new object in "%s"' % cls.name)
            tbl.insert(values=update).execute()
            
        dbs.flush()

        if not quiet:
            # come back
            logger.info('came_from = %s' % came_from)
            if came_from:
                redirect(url(came_from))
                
            else:
                redirect(url('/message', 
                             params=dict(message=_('The record has been successfully saved'),
                                         came_from='')))
        
    @expose('sapns/dashboard/edit.html')
    @require(predicates.not_anonymous())
    def new(self, cls, came_from='/dashboard', **kw):
        
        if not kw:
            kw = {}
            
        kw['came_from'] = came_from
            
        redirect(url('/dashboard/edit/%s' % cls), params=kw)
        
    @expose('sapns/dashboard/edit.html')
    @require(predicates.not_anonymous())
    def edit(self, cls, id='', came_from='/dashboard', **params):
        
        logger = logging.getLogger(__name__ + '/edit')
        
        user = request.identity['user']
        
        # does this user have privilege on this class?
        priv_class = dbs.query(SapnsPrivilege, SapnsClass).\
                join((SapnsClass, 
                      SapnsClass.class_id == SapnsPrivilege.class_id)).\
                filter(and_(SapnsPrivilege.user_id == user.user_id, 
                            SapnsClass.name == cls)).\
                first()
                
        if not priv_class:
            redirect(url('/message',
                         params=dict(message=_('Sorry, you do not have privilege on this class'),
                                     came_from=came_from)))
            
        __, class_ = priv_class
        
        meta = MetaData(dbs.bind)
        try:
            tbl = Table(cls, meta, autoload=True)
            
        except NoSuchTableError:
            redirect(url('/message',
                         params=dict(message=_('This class does not exist'),
                                     came_from=came_from)))
            
        date_fmt = config.get('grid.date_format', default='%m/%d/%Y')
        
        default_values_ro = {}
        default_values = {}
        for field_name, value in params.iteritems():
            # default read-only values (_xxxx)
            m = re.search(r'^_([a-z]\w+)$', field_name, re.I | re.U)
            if m:
                logger.info('Default value (read-only): %s = %s' % (m.group(1), params[field_name]))
                default_values_ro[m.group(1)] = params[field_name]
                
            else:
                # default read/write values (__xxxx)
                # depends on privilege of this attribute
                m = re.search(r'^__([a-z]\w+)$', field_name, re.I | re.U)
                if m:
                    logger.info('Default value (read/write*): %s = %s' % (m.group(1), params[field_name]))
                    default_values[m.group(1)] = params[field_name]
                
        ref = None
        row = None
        if id:
            row = dbs.execute(tbl.select(tbl.c.id == id)).fetchone()
            if not row:
                # row does not exist
                redirect(url('/message',
                             params=dict(message=_('Record does not exist'),
                                         came_from=came_from)))
                
            # reference
            ref = SapnsClass.object_title(class_.name, id)
            
        # get attributes
        attributes = []
        for attr, attr_priv in dbs.query(SapnsAttribute, SapnsAttrPrivilege).\
                join((SapnsClass, 
                      SapnsClass.class_id == SapnsAttribute.class_id)).\
                join((SapnsAttrPrivilege, 
                      and_(SapnsAttrPrivilege.user_id == user.user_id,
                           SapnsAttrPrivilege.attribute_id == SapnsAttribute.attribute_id))).\
                filter(and_(SapnsClass.name == cls,
                            SapnsAttribute.visible == True)).\
                order_by(SapnsAttribute.insertion_order):
            
            value = ''
            read_only = attr_priv.access == SapnsAttrPrivilege.ACCESS_READONLY
            if attr.name in default_values_ro:
                value = default_values_ro[attr.name]
                read_only = True
                
            elif attr.name in default_values:
                value = default_values[attr.name]

            elif row:
                if row[attr.name]:
                    # date
                    if attr.type == SapnsAttribute.TYPE_DATE:
                        value = datetostr(row[attr.name], fmt=date_fmt)
                    
                    # rest of types
                    else:
                        value = row[attr.name] or ''
                        
            attribute = dict(name=attr.name, title=attr.title,
                             type=attr.type, value=value, required=attr.required,
                             related_class=None, related_class_title='',
                             read_only=read_only, vals=None)
            
            logger.info('%s = %s' % (attr.name, repr(value)))
            
            attributes.append(attribute)
            
            if attr.related_class_id:
                # vals
                #attributes[-1]['vals'] = []
                #attribute['vals'] = []
                try:
                    rel_class = dbs.query(SapnsClass).get(attr.related_class_id)
                    
                    # related_class
                    attribute['related_class'] = rel_class.name
                    attribute['related_class_title'] = rel_class.title
                    attribute['related_title'] = SapnsClass.object_title(rel_class.name, value)
                    
                    #logger.info(rel_class.name)
                    #attributes[-1]['vals'] = SapnsClass.class_titles(rel_class.name)
                
                except Exception, e:
                    logger.error(e)
#                    attributes[-1]['vals'] = None
                    attribute['vals'] = None
            
        return dict(cls=cls, title=class_.title, id=id, 
                    related_classes=class_.related_classes(), 
                    attributes=attributes, reference=ref, 
                    came_from=url(came_from))
    
    @expose('sapns/dashboard/delete.html')
    @expose('json')
    def delete(self, cls='', id=None, came_from='/dashboard'):
        
        logger = logging.getLogger(__name__ + '/delete')
        rel_tables = []
        try:
            user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
            
            # check privilege on this class
            if not user.has_privilege(cls):
                return dict(status=False,
                            message=_('Sorry, you do not have privilege on this class'))
            
            # does the record exist?
            meta = MetaData(dbs.bind)
            tbl = Table(cls, meta, autoload=True)
            
            this_record = dbs.execute(tbl.select(tbl.c.id == id)).fetchone()
            if not this_record:
                return dict(status=False, message=_('Record does not exist'))

            # look for objects in other classes that are related with this
            cls = SapnsClass.by_name(cls)
            rel_classes = cls.related_classes()
            for rcls in rel_classes:
                
                logger.info('Related class: "%s.%s"' % (rcls['name'], rcls['attr_name']))
                rtbl = Table(rcls['name'], meta, autoload=True)
                attr_name = rcls['attr_name']
                
                sel = rtbl.select(whereclause=rtbl.c[attr_name] == int(id))
                robj = dbs.execute(sel).fetchone()
                
                if robj != None:
                    rel_tables.append(dict(class_title=rcls['title'],
                                           attr_title=rcls['attr_title']))
                    
                else:
                    logger.info('---No related objects have been found')
                    
            # delete record
            tbl.delete(tbl.c.id == id).execute()
            dbs.flush()
            
            # success!
            return dict(status=True)
            
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e), rel_tables=rel_tables)
        
    @expose('sapns/order/insert.html')
    @require(predicates.has_permission('manage'))
    def ins_order(self, cls='', came_from='/dashboard'):
        
        user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
        
        # check privilege on this class
        if not user.has_privilege(cls):
            redirect(url('/message',
                         params=dict(message=_('Sorry, you do not have privilege on this class'),
                                     came_from=came_from)))
            
        class_ = SapnsClass.by_name(cls)
        
        return dict(page='insertion order', insertion=class_.insertion(),
                    title=class_.title, came_from=url(came_from))

    @expose()
    def ins_order_save(self, attributes='', title='', came_from=''):
        
        # save insertion order
        attributes = sj.loads(attributes)
        
        title_saved = False
        
        cls_title = None
        for attr in attributes:
            
            attribute = dbs.query(SapnsAttribute).get(attr['id'])
            
            if not cls_title:
                cls_title = attribute.class_.title
            
            attribute.title = attr['title']
            attribute.insertion_order = attr['order']
            attribute.required = attr['required']
            attribute.visible = attr['visible']
            
            dbs.add(attribute)
            
            if not title_saved:
                title_saved = True
                attribute.class_.title = title
                dbs.add(attribute.class_)
            
            dbs.flush()
        
        if came_from:
            redirect(url(came_from))
            
        else:
            redirect(url('/message', 
                         params=dict(message=_('Insertion order for "%s" has been successfully updated' % cls_title), 
                                     came_from='')))
    
    @expose('sapns/order/reference.html')
    @require(predicates.has_permission('manage'))
    def ref_order(self, cls, came_from=''):
        
        user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
        
        # check privilege on this class
        if not user.has_privilege(cls):
            redirect(url('/message',
                         params=dict(message=_('Sorry, you do not have privilege on this class'),
                                     came_from=came_from)))
            
        class_ = SapnsClass.by_name(cls)
        
        return dict(page='reference order', reference=class_.reference(all=True), 
                    came_from=came_from)
    
    @expose()
    def ref_order_save(self, attributes='', came_from=''):
        
        # save reference order
        attributes = sj.loads(attributes)
        
        cls_title = None
        for attr in attributes:
            attribute = dbs.query(SapnsAttribute).get(attr['id'])
            
            if not cls_title:
                cls_title = attribute.class_.title
            
            attribute.reference_order = attr['order']
            dbs.add(attribute)
            dbs.flush()
        
        if came_from:
            redirect(url(came_from))
            
        else:
            redirect(url('/message', 
                         params=dict(message=_('Reference order for "%s" has been successfully update' % cls_title), 
                                     came_from='')))