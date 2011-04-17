# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, request, redirect, config
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tg.i18n import set_lang, get_lang
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController
from repoze.what import predicates

from sapns.lib.base import BaseController
from sapns.model import DBSession
from sapns import model
from sapns.controllers.secure import SecureController
import sapns.config.app_cfg as app_cfg

from neptuno.postgres.search import search

from sapns.controllers.error import ErrorController
from sapns.controllers.views import ViewsController
from tg.controllers.util import urlencode
from sapns.controllers.util import UtilController
from sapns.model.sapnsmodel import SapnsUser, SapnsShortcut, SapnsClass,\
    SapnsPrivilege, SapnsAttribute, SapnsAttrPrivilege
from sqlalchemy.exc import NoSuchTableError

import logging
from sqlalchemy import Table
from sqlalchemy.schema import MetaData
from sqlalchemy.sql.expression import and_
#import simplejson as sj

__all__ = ['RootController']


class RootController(BaseController):
    """
    The root controller for the sapns application.

    All the other controllers and WSGI applications should be mounted on this
    controller. For example::

        panel = ControlPanelController()
        another_app = AnotherWSGIApplication()

    Keep in mind that WSGI applications shouldn't be mounted directly: They
    must be wrapped around with :class:`tg.controllers.WSGIAppController`.

    """
    secc = SecureController()

    #admin = AdminController(model, DBSession, config_type=TGAdminConfig)

    error = ErrorController()
    
    views = ViewsController()
    
    util = UtilController()

    @expose('index.html')
    @require(predicates.not_anonymous())
    def index(self, sc_type='list', sc_parent=None):
        curr_lang = get_lang()

        # connected user
        user = DBSession.query(SapnsUser).get(request.identity['user'].user_id)

        # get children shortcuts (shortcuts.parent_id = sc_parent) of the this user
        shortcuts = user.get_shortcuts(id_parent=sc_parent)
        
        if sc_parent:
            sc_parent = DBSession.query(SapnsShortcut).get(sc_parent).parent_id
            
        else:
            sc_parent = None
        
        return dict(page='index', curr_lang=curr_lang, 
                    shortcuts=shortcuts, sc_type=sc_type, sc_parent=sc_parent)
        
    @expose()
    def init(self):
        redirect(url('/util/init'))
        
    @expose('message.html')
    @require(predicates.not_anonymous())
    def message(self, message='Error!', came_from='/'):
        return dict(message=message, came_from=url(came_from))

    @expose('environ.html')
    def environ(self):
        """This method showcases TG's access to the wsgi environment."""
        return dict(environment=request.environ)

    @expose('authentication.html')
    def auth(self):
        """Display some information about auth* on this application."""
        return dict(page='auth')

    @expose('login.html')
    def login(self, came_from=url('/')):
        """Start the user login."""
        login_counter = request.environ['repoze.who.logins']
        if login_counter > 0:
            flash(_('Wrong credentials'), 'warning')
        return dict(page='login', login_counter=str(login_counter),
                    came_from=came_from)

    @expose()
    def post_login(self, came_from='/'):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.

        """
        if not request.identity:
            login_counter = request.environ['repoze.who.logins'] + 1
            redirect('/login', came_from=came_from, __logins=login_counter)
        userid = request.identity['repoze.who.userid']
        flash(_('Welcome back, %s!') % userid)
        redirect(came_from)

    @expose()
    def post_logout(self, came_from=url('/')):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.

        """
        flash(_('We hope to see you soon!'))
        redirect(came_from)

    @expose('listof.html')
    @require(predicates.not_anonymous())
    def list(self, cls='', q='', rp=10, pag_n=1, caption='', show_ids='false', 
             came_from='/'):
        
        logger = logging.getLogger('list')
        
        # does this user have permission on this table?
        user = DBSession.query(SapnsUser).get(request.identity['user'].user_id)
        
        if not user.has_privilege(cls):
            redirect(url('/message',
                         dict(message=_('Sorry, you do not have privilege on this class'),
                              came_from=came_from)))
        
        rp = int(rp)
        pag_n = int(pag_n)
        show_ids = (True if show_ids.lower() == 'true' else False)
        
        pos = (pag_n-1) * rp

        meta = MetaData(bind=DBSession.bind)
        
        try:
            # TODO: cambiar "vista_busqueda_" por "_view_"
            Table('vista_busqueda_%s' % cls, meta, autoload=True)
            view = 'vista_busqueda_%s' % cls
            
        except NoSuchTableError:
            view = cls
            
        ds = search(DBSession, view, q=q.encode('utf-8'), rp=rp, offset=pos, 
                    show_ids=show_ids)
        
        # Reading global settings
        ds.date_fmt = config.get('grid.date_format', default='%m/%d/%Y')
        ds.time_fmt = config.get('grid.time_format', default='%H:%M')
        ds.true_const = config.get('grid.true_const', default='Yes')
        ds.false_const = config.get('grid.false_const', default='No')
        
        ds.float_fmt = app_cfg.format_float
        
        data = ds.to_data()
        
        cols = []
        for col in ds.labels:
            w = 120
            if col == 'id':
                w = 60
                
            cols.append(dict(title=col,
                             width=w,
                             align='center'))
        
        # actions for this class
        class_ = DBSession.query(SapnsClass).\
                    filter(SapnsClass.name == cls).\
                    first()
                    
        actions = class_.sorted_actions()
        
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
            
        return dict(page='list',
                    q=q,
                    show_ids=show_ids,
                    came_from=url(came_from),
                    link='/list?' + urlencode(dict(cls=cls, q=q, rp=rp, pag_n=pag_n,
                                                   caption=caption, show_ids=show_ids)),
                    grid=dict(caption=caption, name=cls,
                              cls=cls,
                              search_url=url('/list'), 
                              cols=cols, data=data, 
                              actions=actions, pag_n=pag_n, rp=rp, pos=pos,
                              totalp=totalp, total=ds.count, total_pag=total_pag))
        
    @expose()
    def setlang(self, lang='en', came_from='/'):
        set_lang(lang)
        redirect(came_from)
        
    def data(self, cls='', id=None):
        pass
    
    def save(self, cls='', id=None):
        pass
    
    @expose('edit.html')
    @require(predicates.not_anonymous())
    def edit(self, cls='', id=None, came_from='/'):
        
        user = request.identity['user']
        
        # does this user have privilege on this class?
        priv = DBSession.query(SapnsPrivilege).\
                join((SapnsClass, 
                      SapnsClass.class_id == SapnsPrivilege.class_id)).\
                filter(and_(SapnsPrivilege.user_id == user.user_id, 
                            SapnsClass.name == cls)).\
                first()
                
        if not priv:
            redirect(url('/message', 
                         dict(message=_('Sorry, you do not have privilege on this class'),
                              came_from=came_from)))
        
        meta = MetaData(DBSession.bind)
        try:
            tbl = Table(cls, meta, autoload=True)
            
        except NoSuchTableError:
            redirect(url('/message', 
                         dict(message=_('This class does not exist'),
                              came_from=came_from)))
        
        if id:
            row = DBSession.execute(tbl.select(tbl.c.id == id)).fetchone()
            if not row:
                # row does not exist
                redirect(url('/message', 
                             dict(message=_('Record does not exist'),
                                  came_from=came_from)))
            
        # get attributes
        attributes = []
        for atr in DBSession.query(SapnsAttribute).\
                join((SapnsClass, SapnsClass.class_id == SapnsAttribute.class_id)).\
                join((SapnsAttrPrivilege, 
                      and_(SapnsAttrPrivilege.user_id == user.user_id,
                           SapnsAttrPrivilege.attribute_id == SapnsAttribute.attribute_id))).\
                filter(and_(SapnsClass.name == cls)).\
                order_by(SapnsAttribute.insertion_order).\
                all():
            
            attributes.append(dict(name=atr.name, title=atr.title, 
                                   type=atr.type, value=row[atr.name] or ''))
            
        return dict(cls=cls, id=id, attributes=attributes, 
                    came_from=url(came_from))
    
    @expose('delete.html')
    def delete(self, cls='', id=None, q=False, came_from='/'):
        
        # does the record exist?
        meta = MetaData(DBSession.bind)
        tbl = Table(cls, meta, autoload=True)
        
        this_record = DBSession.execute(tbl.select(tbl.c.id == id)).fetchone()
        if not this_record:
            # record does not exist
            redirect(url('/message', 
                         dict(message=_('Record does not exist'),
                              came_from=came_from)))
        
        if not q:
            # redirect to the question page
            return dict(cls=cls, id=id, came_from=url(came_from))
            
        # delete record
        tbl.delete(tbl.c.id == id).execute()
        
        redirect(url('/message',
                     dict(message=_('Record was successfully deleted'),
                          came_from=url(came_from))))
        
        redirect(url(came_from))