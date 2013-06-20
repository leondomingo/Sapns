# -*- coding: utf-8 -*-
"""Main Controller"""

from pylons.i18n import ugettext as _
from sapns.controllers.dashboard import DashboardController
from sapns.controllers.docs import DocsController
from sapns.controllers.error import ErrorController
from sapns.controllers.api import APIController
from sapns.lib.base import BaseController
from sapns.lib.sapns.forgot_password import EUserDoesNotExist
from sapns.lib.sapns.util import add_language, save_language, log_access
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser
from tg import expose, require, url, request, response, redirect, config, predicates
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
    api = APIController()

    def __init__(self, *args, **kwargs):
        super(RootController, self).__init__(*args, **kwargs)
        config['pylons.app_globals'].jinja2_env.autoescape = False
    
    @expose('sapns/login.html')
    @expose('sapns/index.html', custom_format='home')
    @add_language
    @log_access('root')
    def index(self, **kw):

        _logger = logging.getLogger('RootController.index')
        
        came_from = kw.get('came_from')
        
        # am I logged?
        if request.identity:
            use_custom_format(self.index, 'home')
            
            if came_from:
                # redirect to the place before logout
                #redirect(came_from)
                redirect(url('/init', params=dict(came_from=came_from)))
                
            else:
                redirection = None

                # redirect to user's entry-point
                user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
                ep = user.entry_point()
                if ep and ep != '/':
                    # redirect(url(ep))
                    redirection = url(ep)
                    
                else:
                    # there is no "entry_point" defined, redirect to default entry-point (app.home)
                    home = config.get('app.home')
                    if home and home != '/':
                        # redirect(url(home))
                        redirection = url(home)

                redirect(url('/init', params=dict(came_from=redirection)))
                
            return dict()
            
        else:
            login_counter = kw.get('login_counter', '0')
            logout = kw.get('logout', '0')

            # read "origin_url" cookie
            origin = request.cookies.get('origin_url')
            if logout == '1' and origin:
                # set "origin_url" cookie to empty string
                response.set_cookie('origin_url', value='', max_age=60*60*24*30*365) # 1 year

                # redirect to "origin_url"
                redirect(url(origin))

            else:
                # get "origin" param
                origin = kw.get('origin', '')

                # save "origin_url" cookie
                response.set_cookie('origin_url', value=origin, max_age=60*60*24*30*365) # 1 year

            return dict(login_counter=login_counter, came_from=came_from or url('/'), origin=origin)
        
    @expose()
    def login(self, **kw):
        # simply redirects to index
        redirect('/', **kw)
            
    @expose('sapns/init.html')
    @require(predicates.not_anonymous())
    def init(self, **kw):
        return dict(came_from=kw.get('came_from', '/'))
        
    @expose('sapns/message.html')
    @require(predicates.not_anonymous())
    def message(self, message='Error!', came_from='/', **kw):
        return dict(message=message, came_from=url(came_from),
                    no_header=kw.get('no_header', False),
                    no_footer=kw.get('no_footer', False),
                    )

    @expose()
    @log_access('login')
    def post_login(self, came_from='/'):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.
        """
        if not request.identity:
            login_counter = request.environ['repoze.who.logins'] + 1
            origin = request.cookies.get('origin_url')
            redirect('/', dict(login_counter=login_counter, came_from=came_from, origin=origin))
            
        redirect(url('/init', params=dict(came_from=came_from)))

    @expose()
    def post_logout(self, came_from=url('/')):
        """
        Redirect the user to the initially requested page on logout
        """
        redirect('/', dict(came_from=came_from, logout=1))

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
