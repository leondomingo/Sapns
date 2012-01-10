# -*- coding: utf-8 -*-
"""Main Controller"""

from jinja2.environment import Environment
from jinja2.loaders import PackageLoader
from pylons.i18n import ugettext as _
from repoze.what import predicates
from sapns.controllers.dashboard import DashboardController
from sapns.controllers.error import ErrorController
from sapns.lib.base import BaseController
from sapns.lib.sapns.util import save_language, init_lang, get_languages
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser
from sqlalchemy.sql.expression import or_, func
from tg import expose, require, url, request, redirect, config
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
            
        return dict(lang=init_lang())
        
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
#        if login_counter > 0:
#            flash(_('Wrong credentials'), 'warning')
            
        return dict(page='', login_counter=str(login_counter),
                    came_from_=came_from, lang=init_lang(),
                    languages=get_languages())

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
        redirect(came_from)

    @expose()
    def post_logout(self, came_from=url('/')):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.
        """
        #flash(_('We hope to see you soon!'))
        redirect(came_from)

    @expose()
    def setlang(self, lang='en'):
        save_language(lang)
        set_lang(lang)
        
    @expose('json')
    def remember_password(self, username_or_email):
        
        from neptuno.enviaremail import enviar_email
        import random
        import hashlib as hl
        
        logger = logging.getLogger('RootController.remember_passsword')
        try:
            u = dbs.query(SapnsUser).\
                filter(or_(func.upper(SapnsUser.user_name) == func.upper(username_or_email),
                           func.upper(SapnsUser.email_address) == func.upper(username_or_email),
                           )).\
                first()
                
            if not u:
                return dict(status=False, 
                            message=_('No user has been found'))
                
            # generate a random password
            random.seed()
            s1 = hl.sha1('%6.6d' % random.randint(0, 999999))
            
            new_password = ''
            for c in s1.hexdigest()[:random.randint(10, 15)]:
                if random.randint(0, 1):
                    new_password += c.upper()
                    
                else:
                    new_password += c
            
            u.password = new_password
            dbs.add(u)
            dbs.flush()
            
            dst = [(u.email_address.encode('utf-8'), u.user_name.encode('utf-8'),)]
                
            # e-mail settings
            remitente = (config.get('avisos.e_mail'), config.get('avisos.nombre'),)
            
            # get e-mail templates
            lang = init_lang()
            root_folder = config.get('app.root_folder')
            env = Environment(loader=PackageLoader('sapns', 'templates'))
            
            try:
                m = __import__('sapns.lib.%s.forgot_password' % root_folder, fromlist=['ForgotPassword'])
                fp = m.ForgotPassword(lang)
                asunto, mensaje, mensaje_html = fp()
                
            except ImportError:
                vars_ = dict(user_name=u.display_name,
                             new_password=new_password,
                             app_title=config.get('avisos.nombre').decode('utf-8'),
                             )
                
                asunto = env.get_template('sapns/users/forgot_password/%s/subject.txt' % lang)
                asunto = asunto.render(**vars_).encode('utf-8')
                
                mensaje = env.get_template('sapns/users/forgot_password/%s/message.txt' % lang)
                mensaje = mensaje.render(**vars_).encode('utf-8')
                
                mensaje_html = env.get_template('sapns/users/forgot_password/%s/message.html' % lang)
                mensaje_html = mensaje_html.render(**vars_).encode('utf-8')
            
            email_login = config.get('avisos.login')
            email_password = config.get('avisos.password')
            
            # send e-mail
            enviar_email(remitente, dst, asunto, mensaje, 
                         config.get('avisos.smtp'), email_login, email_password, 
                         html=mensaje_html, charset='utf-8')
            
            return dict(status=True)
    
        except Exception, e:
            logger.error(e)
            return dict(status=False)