# -*- coding: utf-8 -*-

from neptuno.util import get_paramw
from pylons.i18n import ugettext as _
from sapns.lib.sapns.util import pagination, format_float as _format_float, strtodate as _strtodate
from sapns.lib.sapns.views import filter_sql
from sapns.model import DBSession as dbs, SapnsUser, SapnsClass, SapnsPermission
from tg import url, request, config
import logging
import simplejson as sj
from neptuno.postgres.search import Search
from sapns.lib.sapns.mongo import Mongo
from bson.objectid import ObjectId

date_fmt = config.get('formats.date', default='%m/%d/%Y')


class EListForbidden(Exception):
    pass


class List(object):

    def __init__(self, cls, **kw):
        self.logger = logging.getLogger('sapns.lib.sapns.lists.List')

        self.cls = cls
        self.cls_ = SapnsClass.by_name(self.cls, parent=False)
        self.mdb = Mongo().db
        self.view = None
        if self.cls_.view_id:
            self.view = self.mdb.user_views.find_one(dict(_id=ObjectId(self.cls_.view_id)))

        if not self.view:
            self.view = dict(attributes=[],
                             attributes_detail=[],
                             user_filters={},
                             col_widths={})

            self.view['_id'] = self.mdb.user_views.insert(self.view)

            self.cls_.view_id = str(self.view['_id'])
            dbs.add(self.cls_)
            dbs.flush()

        self.kw = kw

        self.q     = get_paramw(kw, 'q', unicode, opcional=True, por_defecto='')
        self.rp    = get_paramw(kw, 'rp', int, opcional=True, por_defecto=10)
        self.pag_n = get_paramw(kw, 'pag_n', int, opcional=True, por_defecto=1)

        self.ds = None

        came_from = kw.get('came_from', '')
        if came_from:
            came_from = url(came_from)

        self.came_from = came_from

        # collections
        self.ch_attr = kw.get('ch_attr')
        self.parent_id = kw.get('parent_id')

    def __call__(self):

        # does this user have permission on this table?
        user = dbs.query(SapnsUser).get(int(request.identity['user'].user_id))
        permissions = request.identity['permissions']
        roles = request.identity['groups']

        cls_ = SapnsClass.by_name(self.cls)
        ch_cls_ = SapnsClass.by_name(self.cls, parent=False)

        if not (user.has_privilege(ch_cls_.name) or user.has_privilege(cls_.name)) or \
                not ('%s#%s' % (ch_cls_.name, SapnsPermission.TYPE_LIST) in permissions or
                     '%s#%s' % (cls_.name, SapnsPermission.TYPE_LIST) in permissions):
            raise EListForbidden(_('Sorry, you do not have privilege on this class'))

        # shift enabled
        shift_enabled_ = u'managers' in roles

        # related classes
        rel_classes = cls_.related_classes()

        # collection
        caption = ch_cls_.title
        if self.ch_attr and self.parent_id:

            p_cls = cls_.attr_by_name(self.ch_attr).related_class
            p_title = SapnsClass.object_title(p_cls.name, self.parent_id)

            caption = _('%s of [%s]') % (ch_cls_.title, p_title)

        # user_filters
        user_filters = self.view.get('user_filters', {}).get(str(request.identity['user'].user_id), [])

        default = False
        for f in user_filters:
            if f['name'] == 'default':
                default = True
                break

        if not default:
            user_filters.insert(0, dict(name='default', query=self.view.get('query', '')))

        if self.q:
            q = self.q.replace('"', '\\\"')

        else:
            query = ''
            if self.view:
                #query = self.view.get('query', '')
                query = user_filters[0]['query']

            q = query

        return dict(page=ch_cls_.title, came_from=self.came_from,
                    grid=dict(cls=ch_cls_.name,
                              caption=caption,
                              q=q,
                              user_filters=sj.dumps(user_filters),
                              rp=self.rp, pag_n=self.pag_n,
                              # collection
                              ch_attr=self.ch_attr, parent_id=self.parent_id,
                              # related classes
                              rel_classes=rel_classes,
                              shift_enabled=shift_enabled_,
                              ))

    def grid(self, ds=None, **kw):
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
        if not ds:
            ds = self.grid_data(**kw)

        self.ds = ds

        # Reading global settings
        ds.date_fmt = date_fmt
        ds.time_fmt = config.get('formats.time', default='%H:%M')
        ds.datetime_fmt = config.get('formats.datetime', default='%m/%d/%Y %H:%M')
        ds.true_const = _('Yes')
        ds.false_const = _('No')

        ds.float_fmt = _format_float

        visible_width = 800
        min_width = visible_width / 6

        default_width = visible_width / len(ds.labels)
        if default_width < min_width:
            default_width = min_width

        view_cols = [default_width] * len(ds.labels)
        if self.view:
            cmp_ = lambda x, y: cmp(x.get('order', 0), y.get('order', 0))
            for i, a in enumerate(sorted(self.view.get('attributes_detail', []), cmp=cmp_)):
                view_cols[i] = a.get('width', default_width)

            # user - col_widths
            user_id = request.identity['user'].user_id
            if self.view.get('col_widths', {}).get(str(user_id)):

                col_widths = self.view['col_widths'][str(user_id)]
                if len(col_widths) < len(view_cols):
                    col_widths += [default_width] * (len(view_cols) - len(col_widths))

                view_cols_ = [default_width]
                for w, w_ in zip(col_widths, view_cols):
                    if w:
                        view_cols_.append(w)

                    else:
                        view_cols_.append(w_)

                view_cols = view_cols_

        cols = []
        for col, w, type_ in zip(ds.labels, view_cols, ds.types):
            align = 'center'
            # int, long, float
            if type_ == 'int' or type_ == 'long' or type_ == 'float':
                align = config.get('alignment.number', 'right')

            # str
            elif type_ == '' or type_ == 'str':
                align = config.get('alignment.text', 'left')

            # date, time
            elif type_ == 'date' or type_ == 'time':
                align = config.get('alignment.date_time', 'center')

            cols.append(dict(title=col, width=w, align=align))

        this_page, total_pag = pagination(self.rp, self.pag_n, ds.count)

        if ds.count == self.rp:
            total_pag = self.pag_n + 1

        return dict(status=True, cols=cols, data=ds.to_data(), styles=[],
                    this_page=this_page, total_count=ds.count, total_pag=total_pag)

    def grid_data(self, **kw):
        try:
            pos = (self.pag_n - 1) * self.rp

            cls_ = SapnsClass.by_name(self.cls)
            ch_cls_ = SapnsClass.by_name(self.cls, parent=False)

            # does this user have permission on this table?
            user = dbs.query(SapnsUser).get(int(request.identity['user'].user_id))
            permissions = request.identity['permissions']

            if not (user.has_privilege(ch_cls_.name) or user.has_privilege(cls_.name)) or \
                    not ('%s#%s' % (ch_cls_.name, SapnsPermission.TYPE_LIST) in permissions or
                         '%s#%s' % (cls_.name, SapnsPermission.TYPE_LIST) in permissions):
                return dict(status=False,
                            message=_('Sorry, you do not have privilege on this class'))

            # get view name
            view_name = user.get_view_name(ch_cls_.name)

            # collection
            col = None
            if self.ch_attr and self.parent_id:
                col = (self.cls, self.ch_attr, self.parent_id,)

            # get dataset
            s = kw.get('search')
            if not s:
                s = Search(dbs, view_name, strtodatef=_strtodate)
                s.apply_qry(self.q.encode('utf-8'))

            # filters
            s.apply_filters(get_paramw(self.kw, 'filters', sj.loads, opcional=True))

            # "deferred" (variable) filters
            if self.view:
                self.logger.debug('"deferred" filters')
                deferred_filters = []
                for af in self.view.get('advanced_filters', []):
                    if af.get('variable'):
                        expression = filter_sql(af['path'], u'"id_%s"' % af['attr'],
                                                af['operator'], af['value'], af['null_value'])

                        self.logger.debug(expression)
                        deferred_filters.append((expression,))

                self.logger.debug('Applying deferred filters (%d)' % len(deferred_filters))
                s.apply_filters(deferred_filters)

            return s(rp=self.rp, offset=pos, collection=col, no_count=True)

        except Exception, e:
            self.logger.error(e)
