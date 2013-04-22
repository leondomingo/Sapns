# -*- coding: utf-8 -*-
"""
Global configuration file for TG2-specific settings in sapns.

This file complements development/deployment.ini.

Please note that **all the argument values are strings**. If you want to
convert them into boolean, for example, you should use the
:func:`paste.deploy.converters.asbool` function, as in::
    
    from paste.deploy.converters import asbool
    setting = asbool(global_conf.get('the_setting'))
 
"""

from sapns import model
from sapns.lib import app_globals, helpers
from tg.configuration import AppConfig
from tg.configuration.auth import TGAuthMetadata
import neptuno.util as np_util
import sapns

#This tells to TurboGears how to retrieve the data for your user
class ApplicationAuthMetadata(TGAuthMetadata):
    def __init__(self, sa_auth):
        self.sa_auth = sa_auth
        
    def get_user(self, identity, userid):
        return self.sa_auth.dbsession.query(self.sa_auth.user_class).filter_by(user_name=userid).first()
    
    def get_groups(self, identity, userid):
        return [g.group_name for g in identity['user'].groups]
    
    def get_permissions(self, identity, userid):
        return [p.permission_name for p in identity['user'].permissions]

class CustomConfig(AppConfig):
    
    def __init__(self):
        super(CustomConfig, self).__init__()
        self.use_toscawidgets = False
        
        self.renderers = []
        
        self.package = sapns
        
        #Enable json in expose
        self.renderers.append('json')
        #Set the default renderer
        self.default_renderer = 'jinja'
        self.renderers.append('jinja')
        self.jinja_extensions = ['jinja2.ext.i18n']
        self.use_dotted_templatenames = False # makes TG 2.1.5 work
        
        #Configure the base SQLALchemy Setup
        self.use_sqlalchemy = True
        self.model = sapns.model #@UndefinedVariable
        self.DBSession = sapns.model.DBSession #@UndefinedVariable
        
        # Configure the authentication backend
        self.auth_backend = 'sqlalchemy'
        self.sa_auth.dbsession = model.DBSession
        self.sa_auth.user_class = model.User
        #self.sa_auth.group_class = model.Group
        #self.sa_auth.permission_class = model.Permission
        self.sa_auth.authmetadata = ApplicationAuthMetadata(self.sa_auth)
        
        # override this if you would like to provide a different who plugin for
        # managing login and logout of your application
        self.sa_auth.form_plugin = None
        
        # override this if you are using a different charset for the login form
        self.sa_auth.charset = 'utf-8'
        
        # You may optionally define a page where you want users to be redirected to
        # on login:
        self.sa_auth.post_login_url = '/post_login'
        
        # You may optionally define a page where you want users to be redirected to
        # on logout:
        self.sa_auth.post_logout_url = '/post_logout'        
    
    def setup_routes(self):
        """Setup the default TG2 routes

        Override this and setup your own routes maps if you want to use
        custom routes.

        It is recommended that you keep the existing application routing in
        tact, and just add new connections to the mapper above the routes_placeholder
        connection.  Lets say you want to add a pylons controller SamplesController,
        inside the controllers/samples.py file of your application.  You would
        augment the app_cfg.py in the following way::

            from routes import Mapper
            from tg.configuration import AppConfig

            class MyAppConfig(AppConfig):
                def setup_routes(self):
                    map = Mapper(directory=config['pylons.paths']['controllers'],
                                always_scan=config['debug'])

                    # Add a Samples route
                    map.connect('/samples/', controller='samples', action=index)

                    # Setup a default route for the root of object dispatch
                    map.connect('*url', controller='root', action='routes_placeholder')

                    config['routes.map'] = map


            base_config = MyAppConfig()

        """
        
        from tg.configuration import config
        from routes.mapper import Mapper

        map_ = Mapper(directory=config['pylons.paths']['controllers'],
                     always_scan=config['debug'])

        # Setup a default route for the root of object dispatch
        controller_ = 'root'
        root_folder = config.get('app.root_folder')
        if root_folder:
            controller_ = '%s/root' % root_folder

        map_.connect('*url', controller=controller_, action='routes_placeholder')

        config['routes.map'] = map_
    
base_config = CustomConfig()
