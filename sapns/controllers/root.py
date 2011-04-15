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
#from pylons.templating import render_jinja2

#import logging
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

    admin = AdminController(model, DBSession, config_type=TGAdminConfig)

    error = ErrorController()
    
    views = ViewsController()
    
    util = UtilController()

    @expose('index.html')
    def index(self, sc_type='list', sc_parent=None):
        curr_lang = get_lang()
        
        # TODO: get children shortcuts (shortcuts.parent_id = sc_parent) of the this user
        pass
        
        shortcuts = []
        
        if not sc_parent:
            shortcuts.append(dict(url='/views', title='Views'))
            shortcuts.append(dict(url='/util/extract_model', title='Extract model'))
            shortcuts.append(dict(url='/views/edit', title='Edit view'))
            shortcuts.append(dict(title='Esto es un grupo', id=100))
            
        elif int(sc_parent) == 100:
            shortcuts.append(dict(url='/', title='Item 1'))
            shortcuts.append(dict(url='/', title='Item 2'))
            shortcuts.append(dict(url='/', title='Item 3'))
            
            sc_parent = None
        
        return dict(page='index', curr_lang=curr_lang, 
                    shortcuts=shortcuts, sc_type=sc_type, sc_parent=sc_parent)

    @expose('environ.html')
    def environ(self):
        """This method showcases TG's access to the wsgi environment."""
        return dict(environment=request.environ)

    @expose('authentication.html')
    def auth(self):
        """Display some information about auth* on this application."""
        return dict(page='auth')

#    @expose('index.html')
#    @require(predicates.has_permission('manage', msg=l_('Only for managers')))
#    def manage_permission_only(self, **kw):
#        """Illustrate how a page for managers only works."""
#        return dict(page='managers stuff')
#
#    @expose('index.html')
#    @require(predicates.is_user('editor', msg=l_('Only for the editor')))
#    def editor_user_only(self, **kw):
#        """Illustrate how a page exclusive for the editor works."""
#        return dict(page='editor stuff')

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
    def list(self, cls='', q='', rp=10, pag_n=1, caption='', show_ids='false', 
             came_from='/'):
        
        # TODO: controlar permiso del usuario sobre la tabla/vista (cls)
        
        #var1 = render_jinja2('pruebas/prueba.txt', extra_vars=dict(mensaje='Hola, mundo!'))
        
        rp = int(rp)
        pag_n = int(pag_n)
        show_ids = (True if show_ids.lower() == 'true' else False)
        
        pos = (pag_n-1) * rp
        ds = search(DBSession, cls, q=q.encode('utf-8'), rp=rp, offset=pos, 
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
        
        # TODO: calcular las acciones
        actions = [dict(title='New', url=url('/clientes/nuevo'), require_id=False),
                   dict(title='Edit', url=url('/clientes/editar'), require_id=True),
                   dict(title='Delete', url=url('/clientes/borrar'), require_id=True),
                   dict(title='Merge', url=url('/clientes/fusionar'), require_id=True),                   
                   ]
        
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
                    came_from=came_from,
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
    
    def delete(self, cls='', id=None):
        pass
        