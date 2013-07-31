# -*- coding: utf-8 -*-
"""Dashboard Controller"""

from neptuno.postgres.search import Search
from neptuno.util import strtobool, strtodate, strtotime, datetostr, get_paramw
from pylons.i18n import ugettext as _
from sapns.controllers.logs import LogsController
from sapns.controllers.messages import MessagesController
from sapns.controllers.privileges import PrivilegesController
from sapns.controllers.roles import RolesController
from sapns.controllers.shortcuts import ShortcutsController
from sapns.controllers.users import UsersController
from sapns.controllers.util import UtilController
from sapns.controllers.views import ViewsController
from sapns.lib.base import BaseController
from sapns.lib.sapns.const_sapns import ROLE_MANAGERS
from sapns.lib.sapns.htmltopdf import url2
from sapns.lib.sapns.lists import EListForbidden
from sapns.lib.sapns.users import get_user
from sapns.lib.sapns.util import add_language, init_lang, get_languages, get_template, topdf, \
    format_float, datetostr as _datetostr, timetostr as _timetostr, get_list, log_access
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser, SapnsShortcut, SapnsClass, \
    SapnsAttribute, SapnsAttrPrivilege, SapnsPermission, SapnsLog
from zope.sqlalchemy import mark_changed
from sqlalchemy import Table
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.schema import MetaData
from tg import response, expose, require, url, request, redirect, config, predicates as p
import tg
from cStringIO import StringIO
import datetime as dt
import logging
import re
import simplejson as sj
from sapns.lib.sapns.mongo import Mongo
from bson.objectid import ObjectId
import sapns.lib.sapns.to_xls as toxls
import sapns.lib.sapns.merge as sapns_merge
from webob.exc import HTTPForbidden

# controllers
__all__ = ['DashboardController']

date_fmt = config.get('formats.date', default='%m/%d/%Y')
_strtodate = lambda s: strtodate(s, fmt=date_fmt, no_exc=True)

datetime_fmt = config.get('formats.datetime', default='%m/%d/%Y %H:%M')

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
    logs = LogsController()

    @expose('sapns/sidebar.html')
    def sidebar(self, **kw):

        # connected user
        user = dbs.query(SapnsUser).get(request.identity['user'].user_id)

        # get children shortcuts (shortcuts.parent_id = sc_parent) of the this user
        shortcuts = user.get_shortcuts(id_parent=None)

        return dict(shortcuts=shortcuts, came_from=kw.get('came_from', ''), home=url(user.entry_point() or '/dashboard'))

    @expose('sapns/shortcuts/list.html')
    @require(p.not_anonymous())
    @add_language
    @log_access('data exploration')
    def data_exploration(self, **kw):

        sc_parent = this_shortcut = get_paramw(kw, 'sc_parent', int, opcional=True)

        if this_shortcut:
            ts = dbs.query(SapnsShortcut).get(this_shortcut)
            this_shortcut = dict(id=ts.shortcut_id, title=_(ts.title))

        else:
            this_shortcut = dict(id=None, title='')

        user_id = get_paramw(kw, 'user_id', int, opcional=True)
        if not user_id:
            user_id = request.identity['user'].user_id

        user = dbs.query(SapnsUser).get(user_id)

        root = user.get_dashboard().shortcut_id
        if this_shortcut['id'] == root:
            redirect(url('/dashboard/?user_id=%d' % user_id))

        sc_parent = dbs.query(SapnsShortcut).get(sc_parent).parent_id

        fin = False
        parents = []
        shortcut_id_ = this_shortcut['id']
        if shortcut_id_:
            parents.append(this_shortcut['title'])
            while not fin:
                parent = dbs.query(SapnsShortcut).get(shortcut_id_).parent
                if parent:
                    parents.insert(0, _(parent.title))
                    shortcut_id_ = parent.shortcut_id

                else:
                    fin = True

        return dict(page=' / '.join(parents), came_from=kw.get('came_from', user.entry_point()),
                    user=dict(id=user_id, display_name=user.display_name),
                    this_shortcut=this_shortcut, sc_parent=sc_parent)

    @expose('sapns/shortcuts/list.html')
    @require(p.not_anonymous())
    @add_language
    @log_access('dashboard')
    def index(self, **kw):
        user_id = get_paramw(kw, 'user_id', int, opcional=True)
        if not user_id:
            user_id =  request.identity['user'].user_id

        user = dbs.query(SapnsUser).get(user_id)

        return dict(came_from=kw.get('came_from'),
                    this_shortcut={}, user=dict(id=user_id, display_name=user.display_name),
                    _came_from=url(user.entry_point() or '/dashboard/'))

    @expose('sapns/dashboard/listof.html')
    @require(p.not_anonymous())
    @add_language
    @log_access('list')
    def list(self, cls, **kw):

        _logger = logging.getLogger('DashboardController.list')

        try:
            proj_name = config.get('app.root_folder')
            if proj_name:
                m = __import__('sapns.lib.%s.list_redirection' % proj_name, None, None, ['REDIRECTIONS'])
                r = m.REDIRECTIONS.get(cls)
                if r:
                    _logger.debug('Redirecting to...%s' % r)
                    redirect(r, params=kw)

        except ImportError:
            pass

        try:
            List = get_list()
            list_ = List(cls, **kw)
            return list_()
        except EListForbidden, e:
            _logger.error(e)
            redirect(url('/message', params=dict(message=str(e), came_from=kw.get('came_from'))))


    @expose('json')
    @require(p.not_anonymous())
    @log_access('list search')
    def grid(self, cls, **kw):

        _logger = logging.getLogger('DashboardController.grid')

        List = get_list()
        list_ = List(cls, **kw)
        return list_.grid()

    @expose('json')
    @require(p.not_anonymous())
    def grid_actions(self, cls, **kw):

        user = dbs.query(SapnsUser).get(int(request.identity['user'].user_id))

        # actions for this class
        cls_ = SapnsClass.by_name(cls)

        actions_ = {}
        for action in cls_.sorted_actions(user.user_id):
            if action['type'] in [SapnsPermission.TYPE_NEW,
                                  SapnsPermission.TYPE_EDIT,
                                  SapnsPermission.TYPE_DELETE,
                                  SapnsPermission.TYPE_DOCS,
                                  SapnsPermission.TYPE_PROCESS,
                                  SapnsPermission.TYPE_MERGE,
                                  ]:

                actions_[action['name']] = action

        ch_cls_ = SapnsClass.by_name(cls, parent=False)
        for action_ch in ch_cls_.sorted_actions(user.user_id):
            if action_ch['type'] in [SapnsPermission.TYPE_NEW,
                                     SapnsPermission.TYPE_EDIT,
                                     SapnsPermission.TYPE_DELETE,
                                     SapnsPermission.TYPE_DOCS,
                                     SapnsPermission.TYPE_PROCESS,
                                     SapnsPermission.TYPE_MERGE,
                                     ]:

                actions_.update({action_ch['name']: action_ch})

        def cmp_act(x, y):
            if x.pos == y.pos:
                return cmp(x.title, y.title)

            else:
                return cmp(x.pos, y.pos)

        return dict(status=True, actions=sorted(actions_.values(), cmp=cmp_act))

    @expose('json')
    @require(p.not_anonymous())
    def save_user_filter(self, **kw):
        logger = logging.getLogger('DashboardController.save_user_filter')
        try:
            cls = get_paramw(kw, 'cls', unicode)
            filter_name = get_paramw(kw, 'filter_name', unicode)
            query = get_paramw(kw, 'query', unicode)

            user_id = request.identity['user'].user_id

            mdb = Mongo().db

            cls_ = SapnsClass.by_name(cls, parent=False)
            view = mdb.user_views.find_one(dict(_id=ObjectId(cls_.view_id)))
            create_view = False
            if not view:
                create_view = True
                view = dict(user_filters={})

            USER_FILTERS = 'user_filters'

            if not view.get(USER_FILTERS):
                view[USER_FILTERS] = {}

            if not view[USER_FILTERS].get(str(user_id)):
                view[USER_FILTERS][str(user_id)] = []

            found = False
            for filter_ in view[USER_FILTERS][str(user_id)]:
                if filter_['name'] == filter_name:
                    found = True
                    filter_['query'] = query

            if not found:
                if filter_name == 'default':
                    view[USER_FILTERS][str(user_id)].insert(0, dict(name=filter_name, query=query))
                else:
                    view[USER_FILTERS][str(user_id)].append(dict(name=filter_name, query=query))

            if create_view:
                view_id = mdb.user_views.insert(view)

                cls_.view_id = str(view_id)
                dbs.add(cls_)
                dbs.flush()

            else:
                mdb.user_views.update(dict(_id=ObjectId(cls_.view_id)),
                                      {'$set': dict(user_filters=view[USER_FILTERS])})

            return dict(status=True)

        except Exception, e:
            logger.error(e)
            return dict(status=False, msg=str(e))

    @expose('json')
    @require(p.not_anonymous())
    def delete_user_filter(self, **kw):
        logger = logging.getLogger('DashboardController.delete_user_filter')
        try:
            cls = get_paramw(kw, 'cls', unicode)
            filter_name = get_paramw(kw, 'filter_name', unicode)

            user_id = request.identity['user'].user_id

            mdb = Mongo().db

            cls_ = SapnsClass.by_name(cls, parent=False)
            view = mdb.user_views.find_one(dict(_id=ObjectId(cls_.view_id)))
            user_filters = []
            for f in view['user_filters'][str(user_id)]:
                if f['name'] != filter_name:
                    user_filters.append(f)

            view['user_filters'][str(user_id)] = user_filters

            mdb.user_views.update(dict(_id=ObjectId(cls_.view_id)),
                                      {'$set': dict(user_filters=view['user_filters'])})


            return dict(status=True)

        except Exception, e:
            logger.error(e)

    @expose('json')
    @require(p.not_anonymous())
    def save_col_width(self, **kw):
        logger = logging.getLogger('DashboardController.save_col_width')
        try:
            cls = get_paramw(kw, 'cls', unicode)
            length = get_paramw(kw, 'length', int)
            col_num = get_paramw(kw, 'col_num', int)
            width = get_paramw(kw, 'width', int)

            user_id = request.identity['user'].user_id

            mdb = Mongo().db

            cls_ = SapnsClass.by_name(cls, parent=False)
            view = mdb.user_views.find_one(dict(_id=ObjectId(cls_.view_id)))
            create_view = False
            if not view:
                create_view = True
                view = dict(user_filters={})

            COL_WIDTHS = 'col_widths'

            if not view.get(COL_WIDTHS):
                view[COL_WIDTHS] = {}

            if not view[COL_WIDTHS].get(str(user_id)):
                view[COL_WIDTHS][str(user_id)] = [0]*length

            view[COL_WIDTHS][str(user_id)][col_num-1] = width

            if create_view:
                view_id = mdb.user_views.insert(view)

                cls_.view_id = str(view_id)
                dbs.add(cls_)
                dbs.flush()

            else:
                mdb.user_views.update(dict(_id=ObjectId(cls_.view_id)),
                                      {'$set': dict(col_widths=view[COL_WIDTHS])})

            return dict(status=True)

        except Exception, e:
            logger.error(e)
            return dict(status=False, msg=str(e))

    @expose()
    @require(p.not_anonymous())
    @log_access('to_csv')
    def to_csv(self, cls, **kw):

        # all records
        kw['rp'] = 0
        List = get_list()
        list_ = List(cls, **kw)
        ds = list_.grid_data()

        fn = re.sub(r'[^a-zA-Z0-9]', '_', cls.capitalize()).encode('utf-8')

        response.content_type = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment;filename=%s.csv' % fn

        return ds.to_csv()

    @expose('json')
    @require(p.not_anonymous())
    def to_xls(self, **kw):
        logger = logging.getLogger('DashboardController.to_xls')
        try:
            # just one record
            kw['rp'] = 1
            cls = get_paramw(kw, 'cls', str)
            del kw['cls']

            List = get_list()
            list_ = List(cls, **kw)
            ds = list_.grid_data()

            kw.update(cls=cls)

            # q: replace " with &quot;
            if kw.get('q'):
                kw['q'] = kw['q'].replace('"', '&quot;')

            tmpl = get_template('sapns/components/sapns.grid/export-dialog.html')
            content = tmpl.render(tg=tg, _=_, ds=ds, data=kw).encode('utf-8')

            return dict(status=True, content=content)

        except Exception, e:
            logger.error(e)
            return dict(status=False)

    @expose()
    @require(p.not_anonymous())
    @log_access('to_xls')
    def to_xls_(self, **kw):

        logger = logging.getLogger('DashboardController.to_xls_')
        logger.debug(kw)

        visible_columns = sj.loads(kw['visible_columns'])

        # group_by
        group_by = sj.loads(kw['group_by'])
        def cmp_(x, y):
            i = visible_columns.index(x)
            j = visible_columns.index(y)
            return cmp(i, j)

        group_by = sorted(group_by, cmp=cmp_)
        group_by_ = [g.replace('_', '') for g in group_by]

        totals = sj.loads(kw['totals'])

        # remove "sorting" items from "q"
        q_ = []
        if kw['q']:
            if group_by:
                for item in kw['q'].split(','):
                    m = re.search(r'^(\+|\-)(\w+)$', item.strip())
                    if m:
                        if m.group(2) in group_by_:
                            continue

                    q_.append(item)

        if group_by:
            kw['q'] = ','.join(['+%s' % g for g in group_by_])
            if len(q_) > 0:
                if kw['q']:
                    kw['q'] += ','

                kw['q'] += ','.join(q_)

        # all records
        kw['rp'] = 0

        cls = get_paramw(kw, 'cls', str)
        del kw['cls']

        List = get_list()
        list_ = List(cls, **kw)
        ds = list_.grid_data()

        title = re.sub(r'[^a-zA-Z0-9]', '_', cls.capitalize()).encode('utf-8')[:25]

        response.content_type = 'application/excel'
        response.headers['Content-Disposition'] = 'attachment;filename=%s.xls' % title

        # generate XLS content into "memory file"
        xl_file = StringIO()
        toxls.to_xls(ds, visible_columns, group_by, totals, title, xl_file)

        return xl_file.getvalue()

    @expose('json')
    @require(p.not_anonymous())
    def to_pdf(self, **kw):
        logger = logging.getLogger('DashboardController.to_pdf')
        try:
            # just one record
            kw['rp'] = 1
            cls = get_paramw(kw, 'cls', str)
            del kw['cls']

            List = get_list()
            list_ = List(cls, **kw)
            ds = list_.grid_data()

            tmpl = get_template('sapns/components/sapns.grid/export-dialog.html')
            content = tmpl.render(tg=tg, _=_, ds=ds)

            return dict(status=True, content=content)

        except Exception, e:
            logger.error(e)
            return dict(status=False)

    @expose()
    @require(p.not_anonymous())
    def to_pdf_(self, **kw):
        logger = logging.getLogger('DashboardController.to_pdf_')
        try:
            # all records
            kw['rp'] = 0
            cls = get_paramw(kw, 'cls', str)
            del kw['cls']

            List = get_list()
            list_ = List(cls, **kw)
            ds = list_.grid_data()

            fn = re.sub(r'[^a-zA-Z0-9]', '_', cls.capitalize()).encode('utf-8')

            if not kw.get('html'):
                response.content_type = 'application/pdf'
                # response.headers['Content-Disposition'] = 'attachment;filename=%s.pdf' % fn
                response.headers['Content-Disposition'] = 'inline;filename=%s.pdf' % fn
            else:
                response.content_type = 'text/html'

            tmpl = get_template('sapns/components/sapns.grid/export-pdf.html')

            content = tmpl.render(tg=tg, _=_, url2=url2,
                                  format_float=format_float,
                                  datetostr=_datetostr, timetostr=_timetostr,
                                  orientation=kw.get('orientation', 'Portrait') or 'Portrait',
                                  visible_columns=kw.get('visible_columns'),
                                  ds=ds, title=fn).encode('utf-8')

            if not kw.get('html'):
                content = topdf(content, orientation=kw.get('orientation'))

            return content

        except Exception, e:
            logger.error(e)
            response.content_type = 'plain/text'
            response.headers['Content-Disposition'] = 'attachment;filename=error'
            return 'error'

    @expose('json')
    @require(p.not_anonymous())
    def title(self, cls, id):
        logger = logging.getLogger('DashboardController.title')
        try:
            try:
                _title = SapnsClass.object_title(cls, int(id))

            except Exception, e:
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
    @log_access('save record')
    def save(self, cls, **params):
        """
        IN
          cls          <unicode>
          params
            id         <int>
            came_from  <unicode>
            fld_*      ???        Fields to be saved
        """

        logger = logging.getLogger('DashboardController.save')
        try:
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

            def _strtodatetime(s, fmt):

                # build regex
                regex = r'^\s*%s\s*$' % (fmt.replace('%d', r'(?P<day>([0-2]?[1-9]|3[0-1]))').\
                                         replace('%m', r'(?P<month>(0?[1-9]|1[0-2]))').\
                                         replace('%Y', r'(?P<year>\d{4})').\
                                         replace('%H', r'(?P<hour>([0-1]?[0-9]|2[0-3]))').\
                                         replace('%M', r'(?P<minute>[0-5][0-9])').\
                                         replace('%S', r'(?P<second>[0-5][0-9])').\
                                         replace(' ', r'\s'))

                m1 = re.search(regex, s)
                if m1:
                    try:
                        day = int(m1.groupdict().get('day') or 1)
                        month = int(m1.groupdict().get('month') or 1)
                        year = int(m1.groupdict().get('year') or 1900)
                        hour = int(m1.groupdict().get('hour') or 0)
                        min_ = int(m1.groupdict().get('minute') or 0)
                        sec = int(m1.groupdict().get('second') or 0)

                        return dt.datetime(year, month, day, hour, min_, sec)

                    except Exception, e:
                        logger.error(e)
                        raise
                else:
                    raise Exception('Invalid type')

            for field_name, field_value in params.iteritems():
                m_field = re.search(r'^fld_(.+)', field_name)
                if m_field:
                    field_name_ = m_field.group(1)
                    attr = cls.attr_by_name(field_name_)
                    if not attr:
                        update[field_name_] = field_value
                        continue

                    #logger.debug(field_name_)

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

                        # datetime
                        elif attr.type == SapnsAttribute.TYPE_DATETIME:
                            if field_value == '':
                                field_value = None
                            else:
                                field_value = _strtodatetime(field_value, datetime_fmt)

                        # string types
                        else:
                            field_value = field_value.strip()

                    update[field_name_] = field_value
                    #logger.debug('%s=%s' % (field_name, field_value))

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
                logger.debug('Updating object [%d] of "%s"' % (update['id'], cls.name))
                dbs.execute(tbl.update(whereclause=tbl.c.id == update['id'], values=update))

            else:
                logger.debug('Inserting new object in "%s"' % cls.name)
                ins = tbl.insert(values=update).returning(tbl.c.id)
                r = dbs.execute(ins)
                is_insert = True

            mark_changed(dbs())
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
            return dict(status=False, message=unicode(e))

        except Exception, e:
            logger.error(e)
            return dict(status=False)

    @expose('sapns/dashboard/edit/edit.html')
    @require(p.not_anonymous())
    @log_access('create record')
    def new(self, cls, came_from='/', **kw):

        if not kw:
            kw = {}

        kw['came_from'] = came_from

        redirect(url('/dashboard/edit/%s' % cls), params=kw)

    @expose('sapns/dashboard/edit/edit.html')
    @require(p.not_anonymous())
    @log_access('edit record')
    def edit(self, cls, id='', **params):

        logger = logging.getLogger('DashboardController.edit')

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
            perm = '%s#%s' % (ch_class_.name, SapnsPermission.TYPE_EDIT) in permissions or \
                   '%s#%s' % (class_.name, SapnsPermission.TYPE_EDIT) in permissions

        else:
            perm = '%s#%s' % (class_.name, SapnsPermission.TYPE_NEW) in permissions or \
                   '%s#%s' % (class_.name, SapnsPermission.TYPE_NEW) in permissions

        if not (user.has_privilege(ch_class_.name) or user.has_privilege(class_.name)) or not perm:
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

        default_values_ro = {}
        default_values = {}
        for field_name, value in params.iteritems():

            # default read-only values (_xxxx)
            m = re.search(r'^_([a-z]\w+)$', field_name, re.I | re.U)
            if m:
                #logger.debug('Default value (read-only): %s = %s' % (m.group(1), params[field_name]))
                default_values_ro[m.group(1)] = params[field_name]

            else:
                # default read/write values (__xxxx)
                # depends on privilege of this attribute
                m = re.search(r'^__([a-z]\w+)$', field_name, re.I | re.U)
                if m:
                    #logger.debug('Default value (read/write*): %s = %s' % (m.group(1), params[field_name]))
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

        #logger.debug(row)

        # get attributes
        attributes = []
        for attr, attr_priv in SapnsClass.by_name(cls).get_attributes(user.user_id):

            #logger.debug('%s [%s]' % (attr.name, attr_priv.access))

            value = ''
            read_only = attr_priv.access == SapnsAttrPrivilege.ACCESS_READONLY
            if attr.name in default_values_ro:
                value = default_values_ro[attr.name]
                read_only = True

            elif attr.name in default_values:
                value = default_values[attr.name]

            elif row:
                #logger.debug(row[attr.name])
                #logger.debug(attr)
                if row[attr.name] != None:
                    # date
                    if attr.type == SapnsAttribute.TYPE_DATE:
                        value = datetostr(row[attr.name], fmt=date_fmt)

                    # datetime
                    elif attr.type == SapnsAttribute.TYPE_DATETIME:
                        value = row[attr.name].strftime(datetime_fmt) if row[attr.name] else ''

                    # numeric (int, float)
                    elif attr.type in [SapnsAttribute.TYPE_INTEGER, SapnsAttribute.TYPE_FLOAT]:
                        value = row[attr.name]

                    # rest of types
                    else:
                        value = row[attr.name] or ''

            attribute = dict(name=attr.name, title=attr.title,
                             type=attr.type, value=value, required=attr.required,
                             related_class=None, related_class_title='',
                             read_only=read_only, vals=None, field_regex=attr.field_regex,)

            #logger.debug('%s = %s' % (attr.name, repr(value)))

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
                    actions=actions, came_from=url(came_from),
                    lang=init_lang(), languages=get_languages())

    @expose('sapns/dashboard/delete.html')
    @expose('json')
    @require(p.not_anonymous())
    @log_access('delete record')
    def delete(self, cls, id_, **kw):

        logger = logging.getLogger('DashboardController.delete')
        rel_tables = []
        try:
            user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
            permissions = request.identity['permissions']
            cls_ = SapnsClass.by_name(cls)
            ch_cls_ = SapnsClass.by_name(cls, parent=False)

            # check privilege on this class
            if not (user.has_privilege(ch_cls_.name) or user.has_privilege(cls_.name)) or \
            not ('%s#%s' % (ch_cls_.name, SapnsPermission.TYPE_DELETE) in permissions or \
                 '%s#%s' % (cls_.name, SapnsPermission.TYPE_DELETE) in permissions):
                return dict(status=False,
                            message=_('Sorry, you do not have privilege on this class'))

            # does the record exist?
            meta = MetaData(dbs.bind)
            tbl = Table(cls_.name, meta, autoload=True)

            try:
                id_ = int(id_)

            except:
                id_ = sj.loads(id_)

            if isinstance(id_, int):
                # int
                this_record = dbs.execute(tbl.select(tbl.c.id == id_)).fetchone()
                if not this_record:
                    return dict(status=False, message=_('Record does not exist'))

            else:
                # array of ints
                these_records = dbs.execute(tbl.select(tbl.c.id.in_(id_))).fetchall()
                if len(these_records) != len(id_):
                    return dict(status=False, message=_('Some records do not exist'))

            # look for objects in other classes that are related with this

            rel_classes = cls_.related_classes()
            for rcls in rel_classes:

                logger.debug('Related class: "%s.%s"' % (rcls['name'], rcls['attr_name']))
                rtbl = Table(rcls['name'], meta, autoload=True)
                attr_name = rcls['attr_name']

                if isinstance(id_, int):
                    # int
                    i = id_

                else:
                    # array of ints
                    i = id_[0]

                sel = rtbl.select(whereclause=rtbl.c[attr_name] == int(i))
                robj = dbs.execute(sel).fetchone()

                if robj != None:
                    rel_tables.append(dict(class_title=rcls['title'],
                                           attr_title=rcls['attr_title']))

                else:
                    logger.debug('---No related objects have been found')

            # delete record
            if isinstance(id_, int):
                # int
                tbl.delete(tbl.c.id == id_).execute()

                # log
                SapnsLog.register(table_name=cls_.name,
                                  row_id=id_,
                                  who=user.user_id,
                                  what=_('delete'),
                                  )

            else:
                # array of int's
                tbl.delete(tbl.c.id.in_(id_)).execute()

                for i in id_:
                    # log
                    SapnsLog.register(table_name=cls_.name,
                                      row_id=i,
                                      who=user.user_id,
                                      what=_('delete'),
                                      )

            dbs.flush()

            # success!
            return dict(status=True)

        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e), rel_tables=rel_tables)

    @expose('sapns/merge/merge.html')
    @require(p.not_anonymous())
    @log_access('merge records (1)')
    def merge(self, **kw):
        cls = get_paramw(kw, 'cls', str)
        id_ = get_paramw(kw, 'id_', int)

        cls_ = SapnsClass.by_name(cls)

        # check permission "<cls>#merge"
        cls_merge = '%s#merge' % cls
        u = get_user()
        if not u.has_permission(cls_merge):
            raise HTTPForbidden(_('You do not have permission'))

        return dict(cls=dict(name=cls, title=cls_.title), id_=id_)

    @expose('json')
    @require(p.not_anonymous())
    @log_access('merge records (2)')
    def merge_(self, **kw):
        logger = logging.getLogger('DashboardController.merge_')
        try:
            cls     = get_paramw(kw, 'cls', str)
            id_     = get_paramw(kw, 'id_', int)
            from_id = get_paramw(kw, 'from_id', int)

            # check permission "<cls>#merge"
            cls_merge = '%s#merge' % cls
            u = get_user()
            if not u.has_permission(cls_merge):
                raise HTTPForbidden(_('You do not have permission'))

            # get permission
            p_merge = SapnsPermission.by_name(cls_merge)
            not_included = None
            merger = None
            if p_merge.data:
                merge_data = sj.loads(p_merge.data)
                not_included = merge_data.get('extra_params', {}).get('not_included')
                merger = merge_data.get('extra_params', {}).get('merger')

            # not_included
            if not_included:
                not_included = not_included.split(',')

            # merger
            if merger:
                logger.debug('Merging with <%s>' % merger)

                pkg = '.'.join(merger.split('.')[:-1]).encode('utf-8')
                func_name = merger.split('.')[-1].encode('utf-8')

                m = __import__(pkg, fromlist=[func_name])

                func = getattr(m, func_name)
                func(cls, id_, [from_id], not_included=not_included)

            else:
                # default
                sapns_merge.merge(cls, id_, [from_id], not_included=not_included)

            return dict(status=True)

        except Exception, e:
            logger.error(e)
            r = dict(status=False)

            if isinstance(e, HTTPForbidden):
                r.update(msg=str(e))

            return r

    @expose('sapns/order/insert.html')
    @require(p.in_group(ROLE_MANAGERS))
    @add_language
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
    @require(p.in_group(ROLE_MANAGERS))
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
    @require(p.in_group(ROLE_MANAGERS))
    @add_language
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

    @expose('json')
    @require(p.in_group(ROLE_MANAGERS))
    def ref_order_save(self, **kw):

        logger = logging.getLogger('DashboardController.ref_order_save')
        try:
            # save reference order
            attributes = get_paramw(kw, 'attributes', sj.loads)

            cls_title = None
            for attr in attributes:
                attribute = dbs.query(SapnsAttribute).get(attr['id'])

                if not cls_title:
                    cls_title = attribute.class_.title

                attribute.reference_order = attr['order']
                dbs.add(attribute)
                dbs.flush()

            return dict(status=True)

        except Exception, e:
            logger.error(e)
            return dict(status=False)

    @expose('json')
    @require(p.in_group(ROLE_MANAGERS))
    def send_mail(self, **kw):
        logger = logging.getLogger('send_mail')
        try:
            name = get_paramw(kw, 'name', unicode)
            address = get_paramw(kw, 'address', unicode)
            subject = get_paramw(kw, 'subject', unicode)
            message = get_paramw(kw, 'message', unicode)

            from cStringIO import StringIO
            from sapns.lib.sapns.sendmail import send_mail

            f = StringIO()
            f.write('this a test')

            send_mail(to=[(address, name)],
                      subject=subject,
                      message_txt=message,
                      delay=0,
                      files=[('this a /text/', f),
                             ('This A tExt.txt', f)])

        except Exception, e:
            logger.error(e)

    @expose('sapns/components/sapns.selector.example.html')
    @require(p.in_group(ROLE_MANAGERS))
    def test_selector(self):
        return {}

    @expose('sapns/components/sapns.grid/grid_test.html')
    @require(p.in_group(ROLE_MANAGERS))
    def test_grid(self, **kw):
        return dict()

    @expose('sapns/example_pdf.html')
    @require(p.in_group(ROLE_MANAGERS))
    def test_pdf(self):
        request.environ['to_pdf'] = 'example_1.pdf'
        return dict(url2=url2)

    @expose('json')
    @require(p.in_group(ROLE_MANAGERS))
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
                    esto_es_una_prueba=u'Hola, mundo!',
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
