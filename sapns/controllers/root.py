# -*- coding: utf-8 -*-
"""Main Controller"""

from pylons.i18n import ugettext as _
from repoze.what import predicates
from sapns.controllers.dashboard import DashboardController
from sapns.controllers.docs import DocsController
from sapns.controllers.error import ErrorController
from sapns.lib.base import BaseController
from sapns.lib.sapns.forgot_password import EUserDoesNotExist
from sapns.lib.sapns.util import add_language, save_language
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser
from tg import expose, require, url, request, redirect, config
from tg.decorators import use_custom_format
from tg.i18n import set_lang
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
    docs = DocsController()
    
    @expose('sapns/login.html')
    @expose('sapns/index.html', custom_format='home')
    @add_language
    def index(self, **kw):
        
        came_from = kw.get('came_from')
        
        # am I logged?
        if request.identity:
            use_custom_format(self.index, 'home')
            
            if came_from:
                # redirect to the place before logout
                redirect(came_from)
                
            else:
                # redirect to user's entry-point
                user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
                ep = user.entry_point()
                if ep and ep != '/':
                    redirect(url(ep))
                    
                else:
                    # there is no "entry_point" defined, redirect to default entry-point (app.home)
                    home = config.get('app.home')
                    if home and home != '/':
                        redirect(url(home))
                
            return dict()
            
        else:
            login_counter = kw.get('login_counter', '0')
            
            return dict(login_counter=login_counter, came_from=came_from or url('/'))
        
    @expose()
    def login(self, **kw):
        # simply redirects to index
        redirect('/', **kw)
            
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

    @expose()
    def post_login(self, came_from='/'):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.
        """
        if not request.identity:
            login_counter = request.environ['repoze.who.logins'] + 1
            redirect('/', dict(login_counter=login_counter, came_from=came_from))
            
        redirect(came_from)

    @expose()
    def post_logout(self, came_from=url('/')):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.
        """
        redirect('/', dict(came_from=came_from))

    @expose()
    def setlang(self, lang='en'):
        save_language(lang)
        set_lang(lang)
        
    @expose('json')
    def remember_password(self, username_or_email, **kw):
        
        logger = logging.getLogger('RootController.remember_passsword')
        try:
            root_folder = config.get('app.root_folder', 'sapns')
            try:
                m = __import__('sapns.lib.%s.forgot_password' % root_folder, fromlist=['ForgotPassword'])
                fp = m.ForgotPassword(username_or_email)
                fp()
                
            except ImportError:
                
                from sapns.lib.sapns.forgot_password import ForgotPassword
                fp = ForgotPassword(username_or_email)
                fp()
                
            return dict(status=True)
        
        except EUserDoesNotExist, e:
            logger.error(e)
            return dict(status=False, message=_('No user has been found'))
    
        except Exception, e:
            logger.error(e)
            return dict(status=False)