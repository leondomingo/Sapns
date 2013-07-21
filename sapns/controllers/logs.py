# -*- coding: utf-8 -*-

from neptuno.postgres.search import Search
from sapns.lib.sapns.const_sapns import ROLE_MANAGERS
from sapns.lib.sapns.mongo import Mongo
from bson.objectid import ObjectId
from neptuno.util import get_paramw
from pylons.i18n import ugettext as _
from sapns.lib.base import BaseController
from sapns.lib.sapns.util import pagination, format_float as _format_float, get_user, \
    datetostr as _datetostr, timetostr as _timetostr, get_template, add_language, \
    strtodate as _strtodate
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser, SapnsClass, SapnsPermission
from sqlalchemy import MetaData, Table
from sqlalchemy.sql.expression import and_
from tg import expose, require, request, config, url, predicates as p_
import tg
import sapns.lib.helpers as h
import logging
import simplejson as sj
import re

__all__ = ['LogsController']

date_fmt = config.get('formats.date')


class LogsController(BaseController):

    @expose('sapns/logs/access_logs/index.html')
    @require(p_.Any(p_.has_permission('access-logs'),
                    p_.in_group(ROLE_MANAGERS)))
    @add_language
    def index(self, **kw):
        u = get_user()
        return dict(page=u'Access logs', came_from=kw.get('came_from', url(u.entry_point())))

    @expose('json')
    @require(p_.Any(p_.has_permission('access-logs'),
                    p_.in_group(ROLE_MANAGERS)))
    def logs_list(self, **kw):
        logger = logging.getLogger('LogsController.logs_list')
        try:
            rp = get_paramw(kw, 'rp', int, opcional=True, por_defecto=100)
            pag = get_paramw(kw, 'pag', int, opcional=True, por_defecto=1)
            pos = (pag - 1) * rp

            mdb = Mongo().db
            logs = []
            search = {}
            fields = get_paramw(kw, 'fields', sj.loads)
            for f in fields:

                col = f['field_name']

                _id = ObjectId(f['log_id'])
                log = mdb['access'].find_one(dict(_id=_id))

                value = log.copy()
                for col_ in col.split('.'):
                    value = value.get(col_)

                if col == 'when.time':
                    m_time = re.search(r'(\d{2}:\d{2})', value)
                    if m_time:
                        time_ = m_time.group(1)
                        value = re.compile(r'^%s' % time_)

                logger.debug(value)
                search[col] = value

            logger.debug(search)

            for item in mdb['access'].find(search).sort([('when_', -1)]).limit(rp).skip(pos):
                logs.append(dict(id=item['_id'],
                                 when=dict(date=_datetostr(item['when_'].date()),
                                           time=_timetostr(item['when_'].time())),
                                 who=dict(id=item['who']['id'],
                                          display_name=item['who']['display_name'],
                                          user_name=item['who']['name'],
                                          roles=item['who']['roles']),
                                 what=item['what'],
                                 request=item['request'],
                                 args_=item['args_'],
                                 kwargs_=item['kwargs_'],
                                 ))

            tmpl = get_template('sapns/logs/access_logs/list.html')
            content = tmpl.render(tg=tg, _=_, h=h, logs=logs).encode('utf-8')

            return dict(status=True, content=content, num_logs=len(logs))

        except Exception, e:
            logger.error(e)
            return dict(status=False)

    @expose('sapns/logs/search.html')
    @require(p_.not_anonymous())
    def search(self, **kw):
        #logger = logging.getLogger('DashboardController.search')
        return dict(table_name=kw.get('table_name'),
                    row_id=kw.get('row_id'))

    @expose('json')
    @require(p_.not_anonymous())
    def grid(self, cls, **params):

        #logger = logging.getLogger('DashboardController.grid')

        # picking up parameters
        q = get_paramw(params, 'q', unicode, opcional=True, por_defecto='')
        rp = get_paramw(params, 'rp', int, opcional=True, por_defecto=10)
        pag_n = get_paramw(params, 'pag_n', int, opcional=True, por_defecto=1)
        pos = (pag_n-1) * rp

        # does this user have permission on this table?
        user = dbs.query(SapnsUser).get(int(request.identity['user'].user_id))
        permissions = request.identity['permissions']

        cls_ = SapnsClass.by_name(cls)
        ch_cls_ = SapnsClass.by_name(cls, parent=False)

        if not user.has_privilege(cls_.name) or \
                not '%s#%s' % (cls_.name, SapnsPermission.TYPE_LIST) in permissions:
            return dict(status=False,
                        message=_('Sorry, you do not have privilege on this class'))

        # get view name
        view = user.get_view_name(ch_cls_.name)

        # get dataset
        s = Search(dbs, view, strtodatef=_strtodate)
        # TODO: joins
        meta = MetaData(bind=dbs.bind)
        t_logs = Table('sp_logs', meta, autoload=True)

        table_name = get_paramw(params, 'table_name', unicode)
        row_id = get_paramw(params, 'row_id', int)

        s.join(t_logs, and_(t_logs.c.id == s.tbl.c.id,
                            t_logs.c.table_name == table_name,
                            t_logs.c.row_id == row_id,
                            ))

        # q
        s.apply_qry(q.encode('utf-8'))

        # ordenar
        #s.order_by(desc(s.tbl.c.id))

        ds = s(rp=rp, offset=pos)

        # Reading global settings
        ds.date_fmt = date_fmt
        ds.time_fmt = config.get('formats.time', default='%H:%M')
        ds.datetime_fmt = config.get('formats.datetime', default='%m/%d/%Y %H:%M')
        ds.true_const = _('Yes')
        ds.false_const = _('No')

        ds.float_fmt = _format_float

        cols = []
        for col in ds.labels:
            w = 125
            if col == 'id':
                w = 60

            cols.append(dict(title=col, width=w, align='center'))

        this_page, total_pag = pagination(rp, pag_n, ds.count)

        return dict(status=True, cols=cols, data=ds.to_data(),
                    this_page=this_page, total_count=ds.count, total_pag=total_pag)
