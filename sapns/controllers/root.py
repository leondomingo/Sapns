# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, request, redirect, config
from pylons.i18n import ugettext as _ #, lazy_ugettext as l_
from tg.i18n import set_lang, get_lang
from repoze.what import predicates

from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser

from sapns.controllers.error import ErrorController
from sapns.controllers.dashboard import DashboardController

import logging

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
    
    error = ErrorController()
    dashboard = DashboardController()

    @expose('sapns/index.html')
    def index(self):
        
        logger = logging.getLogger('RootController.index')
        
        if request.identity:
            user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
            ep = user.entry_point()
            logger.info('entry-point: %s' % ep)
            if ep and ep != '/':
                redirect(url(ep))
            
        # there is no "entry_point" defined
        home = config.get('app.home')
        if home and home != '/':
            redirect(url(home))
            
        curr_lang = get_lang()
        return dict(curr_lang=curr_lang)
        
    @expose()
    def init(self):
        redirect(url('/dashboard/util/init'))
        
    @expose('sapns/message.html')
    @require(predicates.not_anonymous())
    def message(self, message='Error!', came_from='/', **kw):
        return dict(message=message, came_from=url(came_from),
                    no_header=kw.get('no_header', False),
                    no_footer=kw.get('no_footer', False),
                    )

    @expose('sapns/environ.html')
    @require(predicates.has_permission('manage'))
    def environ(self):
        """This method showcases TG's access to the wsgi environment."""
        return dict(environment=request.environ)

    @expose('sapns/login.html')
    def login(self, came_from=url('/')):
        """Start the user login."""
        login_counter = request.environ['repoze.who.logins']
        if login_counter > 0:
            flash(_('Wrong credentials'), 'warning')
        return dict(page='', login_counter=str(login_counter),
                    came_from_=came_from)

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

    @expose()
    def setlang(self, lang='en', **kw):
        set_lang(lang)
        came_from = kw.get('came_from')
        if came_from:
            redirect(url(came_from))