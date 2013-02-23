# -*- coding: utf-8 -*-

from neptuno.util import get_paramw, strtodate
from pylons.i18n import ugettext as _
from sapns.config import app_cfg
from sapns.lib.sapns.util import pagination
from sapns.model import DBSession as dbs, SapnsUser, SapnsClass, SapnsPermission
from tg import url, request, config
import logging
import simplejson as sj
from neptuno.postgres.search import Search
from sapns.lib.sapns.mongo import Mongo
from bson.objectid import ObjectId

date_fmt = config.get('formats.date', default='%m/%d/%Y')
_strtodate = lambda s: strtodate(s, fmt=date_fmt, no_exc=True)

class EListForbidden(Exception):
    pass

class List(object):
    
    def __init__(self, cls, **kw):
        self.logger = logging.getLogger('sapns.lib.sapns.lists.List')
        
        self.cls = cls
        self.cls_ = SapnsClass.by_name(self.cls, parent=False)
        self.mdb = Mongo().db
        self.view = self.mdb.user_views.find_one(dict(_id=ObjectId(self.cls_.view_id)))
        self.kw = kw

        self.q = get_paramw(kw, 'q', unicode, opcional=True, por_defecto='')
        self.rp = get_paramw(kw, 'rp', int, opcional=True, por_defecto=10)
        self.pag_n = get_paramw(kw, 'pag_n', int, opcional=True, por_defecto=1)

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
        not ('%s#%s' % (ch_cls_.name, SapnsPermission.TYPE_LIST) in permissions or \
             '%s#%s' % (cls_.name, SapnsPermission.TYPE_LIST) in permissions):
            raise EListForbidden(_('Sorry, you do not have privilege on this class'))
            
        # shift enabled
        shift_enabled_ = u'managers' in roles

        
        # related classes
        rel_classes = cls_.related_classes()
        
        if self.q:
            q = self.q.replace('"', '\\\"')
            
        else:
            query = ''
            if self.view:
                query = self.view.get('query', '')
                
            q = query            
        
        # collection
        caption = ch_cls_.title
        if self.ch_attr and self.parent_id:
            
            p_cls = cls_.attr_by_name(self.ch_attr).related_class
            p_title = SapnsClass.object_title(p_cls.name, self.parent_id)
            
            caption = _('%s of [%s]') % (ch_cls_.title, p_title)
            
        return dict(page=_('list of %s') % ch_cls_.title.lower(), came_from=self.came_from,
                    grid=dict(cls=ch_cls_.name,
                              caption=caption,
                              q=q,
                              rp=self.rp, pag_n=self.pag_n,
                              # collection
                              ch_attr=self.ch_attr, parent_id=self.parent_id,
                              # related classes
                              rel_classes=rel_classes,
                              shift_enabled=shift_enabled_,
                              ))
        
    def grid(self):
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
        
        ds = self.grid_data()        
        
        # Reading global settings
        ds.date_fmt = date_fmt
        ds.time_fmt = config.get('formats.time', default='%H:%M')
        ds.datetime_fmt = config.get('formats.datetime', default='%m/%d/%Y %H:%M')
        ds.true_const = _('Yes')
        ds.false_const = _('No')
        
        ds.float_fmt = app_cfg.format_float
        
        visible_width = 800
        min_width = visible_width / 6
        
        default_width = visible_width / len(ds.labels)
        if default_width < min_width:
            default_width = min_width
            
        view_cols = [default_width]*len(ds.labels)
        if self.view:
            view_cols = [default_width]
            for a in sorted(self.view['attributes_detail'], cmp=lambda x,y: cmp(x.get('order', 0), y.get('order', 0))):
                view_cols.append(a.get('width', default_width))
        
        cols = []
        for col, w in zip(ds.labels, view_cols):
            cols.append(dict(title=col, width=w, align='center'))
            
        this_page, total_pag = pagination(self.rp, self.pag_n, ds.count)
        
        if ds.count == self.rp:
            total_pag = self.pag_n + 1
        
        return dict(status=True, cols=cols, data=ds.to_data(), styles=[],
                    this_page=this_page, total_count=ds.count, total_pag=total_pag)
        
    def grid_data(self):
        
        _logger = logging.getLogger('DashboardController.grid_data')

        pos = (self.pag_n-1) * self.rp
        
        # filters
        filters = get_paramw(self.kw, 'filters', sj.loads, opcional=True)

        cls_ = SapnsClass.by_name(self.cls)
        ch_cls_ = SapnsClass.by_name(self.cls, parent=False)        
            
        # does this user have permission on this table?
        user = dbs.query(SapnsUser).get(int(request.identity['user'].user_id))
        permissions = request.identity['permissions']
             
        if not (user.has_privilege(ch_cls_.name) or user.has_privilege(cls_.name)) or \
        not ('%s#%s' % (ch_cls_.name, SapnsPermission.TYPE_LIST) in permissions or \
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
        _search = Search(dbs, view_name, strtodatef=_strtodate)
        _search.apply_qry(self.q.encode('utf-8'))
        _search.apply_filters(filters)
        
        return _search(rp=self.rp, offset=pos, collection=col, no_count=True)        