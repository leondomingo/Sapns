# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController
from repoze.what import predicates

from sapns.lib.base import BaseController
from sapns.model import DBSession, metadata
from sapns import model
from sapns.controllers.secure import SecureController

from sapns.controllers.error import ErrorController

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

    @expose('index.html')
    def index(self):
        return dict(page='index')

    @expose('environ.html')
    def environ(self):
        """This method showcases TG's access to the wsgi environment."""
        return dict(environment=request.environ)

    @expose('authentication.html')
    def auth(self):
        """Display some information about auth* on this application."""
        return dict(page='auth')

    @expose('sapns.templates.index')
    @require(predicates.has_permission('manage', msg=l_('Only for managers')))
    def manage_permission_only(self, **kw):
        """Illustrate how a page for managers only works."""
        return dict(page='managers stuff')

    @expose('sapns.templates.index')
    @require(predicates.is_user('editor', msg=l_('Only for the editor')))
    def editor_user_only(self, **kw):
        """Illustrate how a page exclusive for the editor works."""
        return dict(page='editor stuff')

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

    @expose('grid.html')
    def search(self, cls='', q='', rp=10, pag=1):
        
        cols= [dict(title='Nombre',
                    width=150,
                    ),
               dict(title=u'Dirección',
                    width=300,
                    ),
               dict(title=u'Teléfono',
                    width=100,
                    )
              ]
        
        data = [[u'Groucho Marx', u'c/ Alcalá 100, 1ºA', '91 123 123'],
                [u'Albert Einstein', u'c/ Gran Vía, 3º dcha', '91 123 123'],
                [u'Francis Ford Coppola', u'Pso. de la Castellana, 199', '91 123 123'],
                [u'Alfred Hitchcock', u'Pso. de Recoletos 200', '91 123 123'],
                ]
        
        return dict(page='search', cols=cols, data=data)
    
    def data(self, cls='', id=None):
        pass
    
    def save(self, cls='', id=None):
        pass
    
    def delete(self, cls='', id=None):
        pass
        