# -*- coding: utf-8 -*-
"""Dashboard Controller"""

from neptuno.postgres.search import Search 
from neptuno.util import strtobool, strtodate, strtotime, datetostr, get_paramw
from pylons.i18n import ugettext as _
from repoze.what import predicates as p
from sapns.controllers.docs import DocsController
from sapns.controllers.logs import LogsController
from sapns.controllers.messages import MessagesController
from sapns.controllers.privileges import PrivilegesController
from sapns.controllers.roles import RolesController
from sapns.controllers.shortcuts import ShortcutsController
from sapns.controllers.users import UsersController
from sapns.controllers.util import UtilController
from sapns.controllers.views import ViewsController
from sapns.lib.base import BaseController
from sapns.lib.sapns.htmltopdf import url2
from sapns.lib.sapns.util import pagination
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser, SapnsShortcut, SapnsClass, \
    SapnsAttribute, SapnsAttrPrivilege, SapnsPermission, SapnsLog
from sqlalchemy import Table
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.schema import MetaData
from tg import response, expose, require, url, request, redirect, config
from tg.i18n import set_lang, get_lang
import cStringIO
import logging
import re
import sapns.config.app_cfg as app_cfg
import simplejson as sj

# controllers
__all__ = ['DashboardController']

class ECondition(Exception):
    pass

class DashboardController(BaseController):
    """DashboardController manage raw-data editing"""
    
    views = ViewsController()
    util = UtilController()
    users = UsersController()
    roles = RolesController()
    sc = ShortcutsController()
    messages = MessagesController()
    privileges = PrivilegesController()
    docs = DocsController()
    logs = LogsController()

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
        permissions = request.identity['permissions']
        
        cls_ = SapnsClass.by_name(cls)
        ch_cls_ = SapnsClass.by_name(cls, parent=False)        
            
        #logger.info('Parent class: %s' % cls_.name)
        #logger.info('Child class: %s' % ch_cls_.name)
             
        if not user.has_privilege(cls_.name) or \
        not '%s#%s' % (cls_.name, SapnsPermission.TYPE_LIST) in permissions:
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
            
        return dict(page=_('list of %s') % ch_cls_.title.lower(), came_from=came_from, 
                    grid=dict(cls=ch_cls_.name,
                              caption=caption,
                              q=q.replace('"', '\\\"'), rp=rp, pag_n=pag_n,
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
        
        # filters
        filters = get_paramw(params, 'filters', sj.loads, opcional=True)
        
        # does this user have permission on this table?
        user = dbs.query(SapnsUser).get(int(request.identity['user'].user_id))
        permissions = request.identity['permissions']
        
        cls_ = SapnsClass.by_name(cls)
        ch_cls_ = SapnsClass.by_name(cls, parent=False)        
            
        #logger.info('Parent class: %s' % cls_.name)
        #logger.info('Child class: %s' % ch_cls_.name)
             
        if not user.has_privilege(cls_.name) or \
        not '%s#%s' % (cls_.name, SapnsPermission.TYPE_LIST) in permissions:
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
        _search = Search(dbs, view, strtodatef=strtodate_)
        _search.apply_qry(q.encode('utf-8'))
        _search.apply_filters(filters)
        
        ds = _search(rp=rp, offset=pos, collection=col)
        
#        ds = search(dbs, view, q=q.encode('utf-8'), rp=rp, offset=pos, 
#                    strtodatef=strtodate_, collection=col, filters=filters)
                 
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
            
        this_page, total_pag = pagination(rp, pag_n, ds.count)
        
        return dict(status=True, cols=cols, data=ds.to_data(), 
                    this_page=this_page, total_count=ds.count, total_pag=total_pag)
            
    @expose('json')
    @require(p.not_anonymous())
    def grid_actions(self, cls, **kw):
        
        # does this user have permission on this table?
        user = dbs.query(SapnsUser).get(int(request.identity['user'].user_id))
        
        cls_ = SapnsClass.by_name(cls)
             
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
        
        logger = logging.getLogger('DashboardController.search')
        try:
            import random
            random.seed()
            
            logger.info(params)
            
            #params['caption'] = ''
            g = self.list(**params)
            
            logger.info(g)
            g['grid']['name'] = '_%6.6d' % random.randint(0, 999999)
            g['grid']['q'] = get_paramw(params, 'q', unicode, opcional=True)
            g['grid']['filters'] = params.get('filters')
            
            return g
    
        except Exception, e:
            logger.error(e)
            raise
    
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
        
        cls_ = SapnsClass.by_name(cls)
        
        # user/permissions
        user = dbs.query(SapnsUser).get(int(request.identity['user'].user_id))
        permissions = request.identity['permissions']
        
        if not user.has_privilege(cls_.name) or \
        not '%s#%s' % (cls_.name, SapnsPermission.TYPE_LIST) in permissions:
            return dict(status=False, 
                        message=_('Sorry, you do not have privilege on this class'))
        
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
        s = Search(dbs, view, strtodatef=strtodate_)
        s.apply_qry(q.encode('utf-8'))
        ds = s(rp=0, collection=col)
        
        return ds 
    
    @expose(content_type='text/csv')
    @require(p.not_anonymous())
    def tocsv(self, cls, **kw):
        
        cls_ = SapnsClass.by_name(cls)
        
        # user/permissions
        user = dbs.query(SapnsUser).get(int(request.identity['user'].user_id))
        permissions = request.identity['permissions']
        
        if not user.has_privilege(cls_.name) or \
        not '%s#%s' % (cls_.name, SapnsPermission.TYPE_LIST) in permissions:
            return dict(status=False, 
                        message=_('Sorry, you do not have privilege on this class'))
        
        ds = self.export(cls, **kw)
        
        response.headerlist.append(('Content-Disposition',
                                    'attachment;filename=%s.csv' % cls.encode('utf-8')))
        
        return ds.to_csv()
    
    @expose(content_type='application/excel')
    @require(p.not_anonymous())
    def toxls(self, cls, **kw):
        
        cls_ = SapnsClass.by_name(cls)
        
        # user
        user = dbs.query(SapnsUser).get(int(request.identity['user'].user_id))
        permissions = request.identity['permissions']
        
        if not user.has_privilege(cls_.name) or \
        not '%s#%s' % (cls_.name, SapnsPermission.TYPE_LIST) in permissions:
            return dict(status=False, 
                        message=_('Sorry, you do not have privilege on this class'))
        
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
        logger = logging.getLogger('DashboardController.title')
        try:
            try:
                _title = SapnsClass.object_title(cls, int(id))
                
            except Exception, e:
                logger.error(e)
                
                ids = sj.loads(id)
                _title = []
                ot = SapnsClass.ObjectTitle(cls)
                for id_ in ids:
                    _title.append(ot.title(id_))
            
            return dict(status=True, title=_title)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e).decode('utf-8'))        
    
    @expose('json')
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
        try:
            #logger.info(params)
    
            ch_cls = SapnsClass.by_name(cls, parent=False)
            cls = SapnsClass.by_name(cls)
            id_ = get_paramw(params, 'id', int, opcional=True)
            
            # does this user have permission on this table?
            user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
            permissions = request.identity['permissions']
            
            if not user.has_privilege(cls.name) or \
            not '%s#%s' % (cls.name, SapnsPermission.TYPE_EDIT) in permissions:
                return dict(status=False)
    
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
                    if not attr:
                        update[field_name_] = field_value
                        continue
                    
                    #logger.info(field_name_)
                    
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
                    #logger.info('%s=%s' % (field_name, field_value))

            def _exec_post_conditions(moment, app_name, update):
                if app_name:
                    try:
                        m = __import__('sapns.lib.%s.conditions' % app_name, fromlist=['Conditions'])
                        c = m.Conditions()
                        method_name = '%s_save' % ch_cls.name
                        if hasattr(c, method_name):
                            f = getattr(c, method_name)
                            f(moment, update)
                            
                    except ImportError:
                        pass
                        
            _exec_post_conditions('before', 'sapns', update)
            _exec_post_conditions('before', config.get('app.root_folder'), update)
                    
            meta = MetaData(bind=dbs.bind)
            tbl = Table(cls.name, meta, autoload=True)
            
            is_insert = False
            if update.get('id'):
                logger.info('Updating object [%d] of "%s"' % (update['id'], cls.name))
                dbs.execute(tbl.update(whereclause=tbl.c.id == update['id'], values=update))
                
            else:
                logger.info('Inserting new object in "%s"' % cls.name)
                ins = tbl.insert(values=update).returning(tbl.c.id)
                r = dbs.execute(ins)
                is_insert = True
                
            ch_cls.name = ch_cls.name
            dbs.add(ch_cls)
            dbs.flush()

            if not update.get('id'):
                update['id'] = r.fetchone().id
                
            _exec_post_conditions('after', 'sapns', update)
            _exec_post_conditions('after', config.get('app.root_folder'), update)

            # TODO: log
            _desc = _('updating an existing record')
            _what = _('update')
            if is_insert:
                _desc = _('creating a new record')
                _what = _('create')
                
            SapnsLog.register(table_name=ch_cls.name,
                              row_id=update['id'],
                              who=user.user_id,
                              what=_what,
                              description=_desc,
                              )
            
            return dict(status=True)
        
        except ECondition, e:
            logger.error(e)
            return dict(status=False, message=str(e).decode('utf-8'))
    
        except Exception, e:
            logger.error(e)
            return dict(status=False)
        
    @expose('sapns/dashboard/edit/edit.html')
    @require(p.not_anonymous())
    def new(self, cls, came_from='/', **kw):
        
        if not kw:
            kw = {}
            
        kw['came_from'] = came_from
            
        redirect(url('/dashboard/edit/%s' % cls), params=kw)
        
    @expose('sapns/dashboard/edit/edit.html')
    @require(p.not_anonymous())
    def edit(self, cls, id='', **params):
        
        logger = logging.getLogger(__name__ + '/edit')
        
        came_from = get_paramw(params, 'came_from', unicode, opcional=True,
                               por_defecto='/')
        
        user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
        permissions = request.identity['permissions']
        
        class_ = SapnsClass.by_name(cls)
        ch_class_ = SapnsClass.by_name(cls, parent=False)
        
        # log
        _what = _('edit record')
        if not id:
            _what = _('new record')
            _id = None
        else:
            _id = int(id)
            
        SapnsLog.register(table_name=ch_class_.name,
                          row_id=_id,
                          who=user.user_id,
                          what=_what,
                          )

        if id:
            id = int(id)
            #perm = user.has_permission('%s#%s' % (class_.name, SapnsPermission.TYPE_EDIT))
            perm = '%s#%s' % (class_.name, SapnsPermission.TYPE_EDIT) in permissions
        
        else:
            #perm = user.has_permission('%s#%s' % (class_.name, SapnsPermission.TYPE_NEW))
            perm = '%s#%s' % (class_.name, SapnsPermission.TYPE_NEW) in permissions
        
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
        datetime_fmt = config.get('formats.datetime', default='%Y/%m/%d %H:%M:%S')
        
        default_values_ro = {}
        default_values = {}
        for field_name, value in params.iteritems():
            
            # default read-only values (_xxxx)
            m = re.search(r'^_([a-z]\w+)$', field_name, re.I | re.U)
            if m:
                #logger.info('Default value (read-only): %s = %s' % (m.group(1), params[field_name]))
                default_values_ro[m.group(1)] = params[field_name]
                
            else:
                # default read/write values (__xxxx)
                # depends on privilege of this attribute
                m = re.search(r'^__([a-z]\w+)$', field_name, re.I | re.U)
                if m:
                    #logger.info('Default value (read/write*): %s = %s' % (m.group(1), params[field_name]))
                    default_values[m.group(1)] = params[field_name]
                    
        _created = None
        _updated = None
                    
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
            
            if class_.name != u'sp_logs':
                _created = row['_created'].strftime(datetime_fmt) if row['_created'] else None
                _updated = row['_updated'].strftime(datetime_fmt) if row['_updated'] else None
            
        # get attributes
        attributes = []
        for attr, attr_priv in SapnsClass.by_name(cls).get_attributes(user.user_id):
            
            #logger.info('%s [%s]' % (attr.name, attr_priv.access))
            
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
                             read_only=read_only, vals=None, field_regex=attr.field_regex,)
            
            #logger.info('%s = %s' % (attr.name, repr(value)))
            
            attributes.append(attribute)
            
            if attr.related_class_id:
                # vals
                try:
                    rel_class = dbs.query(SapnsClass).get(attr.related_class_id)
                    
                    # related_class
                    attribute['related_class'] = rel_class.name
                    attribute['related_class_title'] = rel_class.title
                    attribute['related_title'] = SapnsClass.object_title(rel_class.name, value)
                    
                except Exception, e:
                    logger.error(e)
                    attribute['vals'] = None
        
        def _exec_pre_conditions(app_name):
            if app_name:
                try:
                    # pre-conditions
                    m = __import__('sapns.lib.%s.conditions' % app_name, fromlist=['Conditions'])
                    c = m.Conditions()
                    method_name = '%s_before' % ch_class_.name
                    if hasattr(c, method_name):
                        f = getattr(c, method_name)
                        f(id, attributes)
                    
                except ImportError:
                    pass
                
        _exec_pre_conditions('sapns')
        _exec_pre_conditions(config.get('app.root_folder'))
                    
        return dict(cls=cls, title=ch_class_.title, id=id, 
                    related_classes=class_.related_classes(),
                    attributes=attributes, reference=ref,
                    _created=_created, _updated=_updated,
                    actions=actions, came_from=url(came_from))
    
    @expose('sapns/dashboard/delete.html')
    @expose('json')
    @require(p.not_anonymous())
    def delete(self, cls, id_, **kw):
        
        #came_from = get_paramw(kw, 'came_from', opcional=True, por_defecto='/')
        
        logger = logging.getLogger(__name__ + '/delete')
        rel_tables = []
        try:
            user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
            permissions = request.identity['permissions']
            cls_ = SapnsClass.by_name(cls)
            
            # check privilege on this class
            if not user.has_privilege(cls_.name) or \
            not '%s#%s' % (cls_.name, SapnsPermission.TYPE_DELETE) in permissions:
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
            
            # log
            SapnsLog.register(table_name=cls_.name,
                              row_id=id_,
                              who=user.user_id,
                              what=_('delete'),
                              )

            # success!
            return dict(status=True)
            
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e), rel_tables=rel_tables)
        
    @expose('sapns/order/insert.html')
    @require(p.in_group(u'managers'))
    def ins_order(self, cls, came_from='/'):
        
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
    def ref_order(self, cls, came_from='/'):
        
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
        return dict()
    
    @expose('sapns/example_pdf.html')
    @require(p.in_group('managers'))
    def test_pdf(self):
        request.environ['to_pdf'] = 'example_1.pdf'
        return dict(url2=url2)
    
    @expose('json')
    @require(p.in_group('managers'))
    def test_search(self, **kw):
        import jinja2
        import random
        random.seed()
        
        s = Search(dbs, '_view_%s' % kw.get('cls'))
        s.apply_qry(kw.get('q').encode('utf-8'))
        ds = s(rp=int(kw.get('rp', 10)))
        
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