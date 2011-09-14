# -*- coding: utf-8 -*-
"""Dashboard Controller"""

from tg import response, expose, require, url, request, redirect, config
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tg.i18n import set_lang, get_lang
from repoze.what import predicates as p

from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs
import sapns.config.app_cfg as app_cfg

# controllers
from sapns.controllers.views import ViewsController
from sapns.controllers.util import UtilController
from sapns.controllers.users import UsersController
from sapns.controllers.shortcuts import ShortcutsController
from sapns.controllers.messages import MessagesController
from sapns.controllers.privileges import PrivilegesController
from sapns.controllers.docs import DocsController

from neptuno.postgres.search import search
from neptuno.util import strtobool, strtodate, strtotime, datetostr, get_paramw

from sapns.model.sapnsmodel import SapnsUser, SapnsShortcut, SapnsClass,\
    SapnsAttribute, SapnsAttrPrivilege, SapnsPermission

import logging
import re
import simplejson as sj #@UnresolvedImport
import cStringIO
from sqlalchemy import Table
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.schema import MetaData

__all__ = ['DashboardController']

class DashboardController(BaseController):
    """DashboardController manage raw-data editing"""
    
    views = ViewsController()
    util = UtilController()
    users = UsersController()
    sc = ShortcutsController()
    messages = MessagesController()
    privileges = PrivilegesController()
    docs = DocsController()

    @expose('sapns/dashboard/index.html')
    @require(p.not_anonymous())
    def index(self, sc_type='list', sc_parent=None):
        curr_lang = get_lang()

        # connected user
        user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
        
        # get children shortcuts (shortcuts.parent_id = sc_parent) of the this user
        shortcuts = user.get_shortcuts(id_parent=sc_parent)
        
        params = {}
        if sc_parent:
            params = dict(sc_parent=sc_parent)
        came_from = url('/dashboard/', params=params)
        
        if sc_parent:
            sc_parent = dbs.query(SapnsShortcut).get(sc_parent).parent_id
            
        else:
            sc_parent = None
            
        # number of messages
        messages = user.messages()
        unread = user.unread_messages()
        
        return dict(page='dashboard', curr_lang=curr_lang, shortcuts=shortcuts,
                    messages=messages, unread=unread,
                    sc_type=sc_type, sc_parent=sc_parent, _came_from=came_from)
        
    @expose()
    def init(self):
        redirect(url('/dashboard/util/init'))

    @expose('sapns/dashboard/listof.html')
    @require(p.not_anonymous())
    def list(self, cls, **params):
        
        #logger = logging.getLogger(__name__ + '/list')
        
        q = get_paramw(params, 'q', unicode, opcional=True, por_defecto='')
        rp = get_paramw(params, 'rp', int, opcional=True, por_defecto=10)
        pag_n = get_paramw(params, 'pag_n', int, opcional=True, por_defecto=1)

        came_from = params.get('came_from', '')
        if came_from:
            came_from = url(came_from)
            
        # collections
        ch_attr = params.get('ch_attr')
        parent_id = params.get('parent_id')
        
        # does this user have permission on this table?
        user = dbs.query(SapnsUser).get(int(request.identity['user'].user_id))
        
        cls_ = SapnsClass.by_name(cls)
        ch_cls_ = SapnsClass.by_name(cls, parent=False)        
            
        #logger.info('Parent class: %s' % cls_.name)
        #logger.info('Child class: %s' % ch_cls_.name)
             
        if not user.has_privilege(cls_.name) or \
        not user.has_permission('%s#%s' % (cls_.name, SapnsPermission.TYPE_LIST)):
            redirect(url('/message', 
                         params=dict(message=_('Sorry, you do not have privilege on this class'),
                                     came_from=came_from)))
        
        # related classes
        rel_classes = cls_.related_classes()
        
        # collection
        caption = ch_cls_.title
        if ch_attr and parent_id:
            
            p_cls = cls_.attr_by_name(ch_attr).related_class
            p_title = SapnsClass.object_title(p_cls.name, parent_id)
            
            caption = _('%s of [%s]') % (ch_cls_.title, p_title)
            
        return dict(page=_('list of %s') % cls_.title.lower(), came_from=came_from, 
                    grid=dict(cls=cls_.name,
                              caption=caption,
                              q=q, rp=rp, pag_n=pag_n,
                              # collection
                              ch_attr=ch_attr, parent_id=parent_id,
                              # related classes
                              rel_classes=rel_classes))
        
    @expose('json')
    @require(p.not_anonymous())
    def grid(self, cls, **params):
        
        #logger = logging.getLogger('DashboardController.grid')

        # picking up parameters
        q = get_paramw(params, 'q', unicode, opcional=True, por_defecto='')
        rp = get_paramw(params, 'rp', int, opcional=True, por_defecto=10)
        pag_n = get_paramw(params, 'pag_n', int, opcional=True, por_defecto=1)
        pos = (pag_n-1) * rp
        
        # collections
        ch_attr = params.get('ch_attr')
        parent_id = params.get('parent_id')
        
        # does this user have permission on this table?
        user = dbs.query(SapnsUser).get(int(request.identity['user'].user_id))
        
        cls_ = SapnsClass.by_name(cls)
        ch_cls_ = SapnsClass.by_name(cls, parent=False)        
            
        #logger.info('Parent class: %s' % cls_.name)
        #logger.info('Child class: %s' % ch_cls_.name)
             
        if not user.has_privilege(cls_.name) or \
        not user.has_permission('%s#%s' % (cls_.name, SapnsPermission.TYPE_LIST)):
            return dict(status=False, 
                        message=_('Sorry, you do not have privilege on this class'))
        
        # get view name
        view = user.get_view_name(ch_cls_.name)
            
        date_fmt = config.get('formats.date', default='%m/%d/%Y')
        strtodate_ = lambda s: strtodate(s, fmt=date_fmt, no_exc=True)
        
        #logger.info('search...%s / q=%s' % (view, q))
        
        # collection
        col = None
        if ch_attr and parent_id:
            col = (cls, ch_attr, parent_id,)

        # get dataset
        ds = search(dbs, view, q=q.encode('utf-8'), rp=rp, offset=pos, 
                    strtodatef=strtodate_, collection=col) 
        
        # Reading global settings
        ds.date_fmt = date_fmt
        ds.time_fmt = config.get('formats.time', default='%H:%M')
        ds.datetime_fmt = config.get('formats.datetime', default='%m/%d/%Y %H:%M')
        ds.true_const = _('Yes')
        ds.false_const = _('No')
        
        ds.float_fmt = app_cfg.format_float
        
        cols = []
        for col in ds.labels:
            w = 125
            if col == 'id':
                w = 60
                
            cols.append(dict(title=col, width=w, align='center'))
        
        # total number of pages
        total_pag = 1
        if rp > 0:
            total_pag = ds.count/rp
            
            if ds.count % rp != 0:
                total_pag += 1
            
            if total_pag == 0:
                total_pag = 1
        
        # rows in this page
        this_page = ds.count - pos
        if rp and this_page > rp:
            this_page = rp
            
        return dict(status=True, cols=cols, data=ds.to_data(), 
                    this_page=this_page, total_count=ds.count, total_pag=total_pag)
            
#        return dict(ch_attr=ch_attr, parent_id=parent_id,
#                    grid=dict(caption=caption, name=cls, cls=cls_.name,
#                              search_url=url('/dashboard/grid/'), 
#                              cols=cols, data=data, 
#                              pag_n=pag_n, rp=rp, pos=pos,
#                              this_page=this_page, total=ds.count, total_pag=total_pag))

    @expose('json')
    @require(p.not_anonymous())
    def grid_actions(self, cls, **kw):
        
        # does this user have permission on this table?
        user = dbs.query(SapnsUser).get(int(request.identity['user'].user_id))
        
        cls_ = SapnsClass.by_name(cls)
        #ch_cls_ = SapnsClass.by_name(cls, parent=False)        
             
        if not user.has_privilege(cls_.name) or \
        not user.has_permission('%s#%s' % (cls_.name, SapnsPermission.TYPE_LIST)):
            return dict(status=False, 
                        message=_('Sorry, you do not have privilege on this class'))
        
        # actions for this class
        actions = cls_.sorted_actions(user.user_id)
        actions = [act for act in actions \
                   if act['type'] in [SapnsPermission.TYPE_NEW,
                                      SapnsPermission.TYPE_EDIT,
                                      SapnsPermission.TYPE_DELETE,
                                      SapnsPermission.TYPE_DOCS,
                                      SapnsPermission.TYPE_PROCESS,
                                     ]]
        
        return dict(status=True, actions=actions)
    
    @expose('sapns/dashboard/search.html')
    @require(p.not_anonymous())
    def search(self, **params):
        
        import random
        random.seed()
        
        logger = logging.getLogger(__name__ + '/search')
        logger.info(params)
        
        #params['caption'] = ''
        g = self.list(**params)
        
        logger.info(g)
        g['grid']['name'] = '_%6.6d' % random.randint(0, 999999)
        
        return g
    
    def export(self, cls, **kw):
        """
        IN
          cls          <unicode>
          kw
            q          <unicode>
            ch_attr    <unicode>
            parent_id  <int>
        """
        
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
            
        view = user.get_view_name(cls)
        
        date_fmt = config.get('formats.date', default='%m/%d/%Y')
        
        strtodate_ = lambda s: strtodate(s, fmt=date_fmt, no_exc=True)
        
        # get dataset
        ds = search(dbs, view, q=q.encode('utf-8'), rp=0, collection=col,
                    strtodatef=strtodate_)
        
        return ds 
    
    @expose(content_type='text/csv')
    @require(p.not_anonymous())
    def tocsv(self, cls, **kw):
        ds = self.export(cls, **kw)
        
        response.headerlist.append(('Content-Disposition',
                                    'attachment;filename=%s.csv' % cls.encode('utf-8')))
        
        return ds.to_csv()
    
    @expose(content_type='application/excel')
    @require(p.not_anonymous())
    def toxls(self, cls, **kw):
        ds = self.export(cls, **kw)

        response.headerlist.append(('Content-Disposition',
                                    'attachment;filename=%s.xls' % cls.encode('utf-8')))
        
        # generate XLS content into "memory file"
        xl_file = cStringIO.StringIO()
        ds.to_xls(cls.capitalize().replace('_', ' '), xl_file)
        
        return xl_file.getvalue()
    
    @expose('json')
    @require(p.not_anonymous())
    def title(self, cls, id):
        logger = logging.getLogger(__name__ + '/title')
        try:
            title = SapnsClass.object_title(cls, id)
            return dict(status=True, title=title)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e).decode('utf-8'))        
    
    @expose()
    @require(p.not_anonymous())
    def save(self, cls, **params):
        """
        IN
          cls          <unicode>
          params
            id         <int>
            came_from  <unicode>
            fld_*      ???        Fields to be saved
        """
        
        logger = logging.getLogger(__name__ + '/save')
        logger.info(params)

        cls = SapnsClass.by_name(cls)
        id_ = get_paramw(params, 'id', int, opcional=True)
        came_from = params.get('came_from') #, '/dashboard/list?cls=%s' % cls.name)
        quiet = strtobool(params.get('quiet', 'false'))
        
        # does this user have permission on this table?
        user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
        
        if not user.has_privilege(cls.name) or \
        not user.has_permission('%s#%s' % (cls.name, SapnsPermission.TYPE_EDIT)):
            redirect(url('/message', 
                         params=dict(message=_('Sorry, you do not have privilege on this class'),
                                     came_from=came_from)))

        # init "update" dictionary
        update = {}
        
        if id_:
            update['id'] = int(id_)
            
        READONLY_DENIED = [SapnsAttrPrivilege.ACCESS_READONLY, 
                           SapnsAttrPrivilege.ACCESS_DENIED]
        
        for field_name, field_value in params.iteritems():
            m_field = re.search(r'^fld_(.+)', field_name)
            if m_field:
                field_name_ = m_field.group(1) 
                attr = cls.attr_by_name(field_name_)
                
                logger.info(field_name_)
                
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
                            
                    elif attr.type == SapnsAttribute.TYPE_DATETIME:
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
            if came_from:
                redirect(url(came_from))
                
            else:
                redirect(url('/message', 
                             params=dict(message=_('The record has been successfully saved'),
                                         came_from='')))
        
    @expose('sapns/dashboard/edit/edit.html')
    @require(p.not_anonymous())
    def new(self, cls, came_from='/dashboard', **kw):
        
        if not kw:
            kw = {}
            
        kw['came_from'] = came_from
            
        redirect(url('/dashboard/edit/%s' % cls), params=kw)
        
    @expose('sapns/dashboard/edit/edit.html')
    @require(p.not_anonymous())
    def edit(self, cls, id='', **params):
        
        logger = logging.getLogger(__name__ + '/edit')
        
        came_from = get_paramw(params, 'came_from', unicode, opcional=True,
                               por_defecto='/dashboard')
        
        user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
        class_ = SapnsClass.by_name(cls)
        
        if id:
            id = int(id)
            perm = user.has_permission('%s#%s' % (cls, SapnsPermission.TYPE_EDIT))
        
        else:
            perm = user.has_permission('%s#%s' % (cls, SapnsPermission.TYPE_NEW))
        
        if not user.has_privilege(class_.name) or not perm:
            redirect(url('/message',
                         params=dict(message=_('Sorry, you do not have privilege on this class'),
                                     came_from=came_from)))

        # actions
        actions = [action for action in class_.sorted_actions(user.user_id) 
                   if action['type']  == 'process']
            
        meta = MetaData(dbs.bind)
        try:
            tbl = Table(class_.name, meta, autoload=True)
            
        except NoSuchTableError:
            redirect(url('/message',
                         params=dict(message=_('This class does not exist'),
                                     came_from=came_from)))
            
        date_fmt = config.get('formats.date', default='%m/%d/%Y')
        
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
        for attr, attr_priv in SapnsClass.by_name(cls).get_attributes(user.user_id):
            
            logger.info('%s [%s]' % (attr.name, attr_priv.access))
            
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
            
            #logger.info('%s = %s' % (attr.name, repr(value)))
            
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
                    actions=actions, came_from=url(came_from))
    
    @expose('sapns/dashboard/delete.html')
    @expose('json')
    @require(p.not_anonymous())
    def delete(self, cls, id_, **kw):
        
        #came_from = get_paramw(kw, 'came_from', opcional=True, por_defecto='/dashboard')
        
        logger = logging.getLogger(__name__ + '/delete')
        rel_tables = []
        try:
            user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
            cls_ = SapnsClass.by_name(cls)
            
            # check privilege on this class
            if not user.has_privilege(cls_.name) or \
            not user.has_permission('%s#%s' % (cls, SapnsPermission.TYPE_DELETE)):
                return dict(status=False,
                            message=_('Sorry, you do not have privilege on this class'))
            
            # does the record exist?
            meta = MetaData(dbs.bind)
            tbl = Table(cls_.name, meta, autoload=True)
            
            this_record = dbs.execute(tbl.select(tbl.c.id == id_)).fetchone()
            if not this_record:
                return dict(status=False, message=_('Record does not exist'))

            # look for objects in other classes that are related with this
            
            rel_classes = cls_.related_classes()
            for rcls in rel_classes:
                
                logger.info('Related class: "%s.%s"' % (rcls['name'], rcls['attr_name']))
                rtbl = Table(rcls['name'], meta, autoload=True)
                attr_name = rcls['attr_name']
                
                sel = rtbl.select(whereclause=rtbl.c[attr_name] == int(id_))
                robj = dbs.execute(sel).fetchone()
                
                if robj != None:
                    rel_tables.append(dict(class_title=rcls['title'],
                                           attr_title=rcls['attr_title']))
                    
                else:
                    logger.info('---No related objects have been found')
                    
            # delete record
            tbl.delete(tbl.c.id == id_).execute()
            dbs.flush()
            
            # success!
            return dict(status=True)
            
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e), rel_tables=rel_tables)
        
    @expose('sapns/order/insert.html')
    @require(p.in_group(u'managers'))
    def ins_order(self, cls, came_from='/dashboard'):
        
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
    @require(p.in_group(u'managers'))
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
                         params=dict(message=_('Insertion order for "%s" has been successfully updated') % cls_title, 
                                     came_from='')))
    
    @expose('sapns/order/reference.html')
    @require(p.in_group(u'managers'))
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
    @require(p.in_group(u'managers'))
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
                         params=dict(message=_('Reference order for "%s" has been successfully updated') % cls_title, 
                                     came_from='')))
            
    @expose('sapns/components/sapns.selector.example.html')
    @require(p.in_group('managers'))
    def test_selector(self):
        return {}
    
    @expose('sapns/components/sapns.grid/grid_test.html')
    @require(p.in_group('managers'))
    def test_grid(self):
        return {}
    
    @expose('json')
    @require(p.in_group('managers'))
    def test_search(self, **kw):
        import jinja2
        import random
        random.seed()
        
        ds = search(dbs, '_view_%s' % kw.get('cls'), q=kw.get('q'), 
                    rp=int(kw.get('rp', 10)))
        
        def r():
            return random.randint(1, 1000) / 1.23
        
        cols = []
        for col in ds.labels:
            cols.append(dict(title=col))
        
        return dict(status=True,
                    cols_=[dict(title='id', width=30),
                          dict(title='ABC', align='right', width=100),
                          dict(title='DEF', width=300),
                          dict(title='GHI', align='left'),
                          dict(title='cuATro'),
                          dict(title='five'),
                          dict(title='SIX', width=200, align='right'),
                         ],
                    cols=cols,
                    data=ds.to_data(),
                    data_=[[kw.get('p1'), r(), r(), r()],
                          [kw.get('p2')],
                          [3, kw.get('q'), 211, 311, 411, 511, 611],
                          [kw.get('rp'), 11, None, kw.get('pos')],
                          [100, u'León', jinja2.escape(u'<!-- -->')],
                          [200, u'€łđŋ', jinja2.escape(u'<a></a>')],
                          [300, jinja2.escape(u'<a href="#">Google</a>')],
                         ])
    
    
