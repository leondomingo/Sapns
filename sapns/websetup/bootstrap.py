# -*- coding: utf-8 -*-
"""Setup the sapns application"""

from sapns import model
import transaction
import logging

def bootstrap(command, conf, vars):
    """Place any commands to setup sapns here"""
    
    logger = logging.getLogger('bootstrap')

    # <websetup.bootstrap.before.auth
    from sqlalchemy.exc import IntegrityError
    try:
        
        logger.info('User "manager"')
        # user
        u = model.User()
        u.user_name = u'manager'
        u.display_name = u'Superuser Of The System'
        u.email_address = u'manager@somedomain.com'
        u.password = u'manager'
    
        model.DBSession.add(u)
    
        logger.info('Role "managers"')
    
        # "managers" role
        managers = model.Group()
        managers.group_name = u'managers'
        managers.display_name = u'Managers Group'
    
        managers.users.append(u)
    
        model.DBSession.add(managers)
        
        # permissions
        p_man = model.SapnsPermission()
        p_man.permission_name = u'manage'
        p_man.display_name = u'manage'
        p_man.description = u'This permission give an administrative right to the bearer'
        p_man.groups.append(managers)
    
        model.DBSession.add(p_man)
        
        p_users = model.SapnsPermission()
        p_users.permission_name = u'users'
        p_users.display_name = u'users'
        p_users.description = u'User management permission'
        p_users.groups.append(managers)
        
        model.DBSession.add(p_users)

        p_views = model.SapnsPermission()
        p_views.permission_name = u'views'
        p_views.display_name = u'views'
        p_views.description = u'Views management permission'
        p_views.groups.append(managers)
        
        model.DBSession.add(p_views)
        
        # permission: utilities
        p_util = model.SapnsPermission()
        p_util.permission_name = u'utilities'
        p_util.display_name = u'utilities'
        p_util.description = u'Utilites'
        p_util.groups.append(managers)
        
        model.DBSession.add(p_util)
        model.DBSession.flush()

        p_util.groups.append(managers)
        model.DBSession.add(p_util)

        # permission: docs        
        p_docs = model.SapnsPermission()
        p_docs.permission_name = u'docs'
        p_docs.display_name = u'docs'
        p_docs.description = u'Documents management'
        p_docs.groups.append(managers)
        
        model.DBSession.add(p_docs)

        # repo (docs)
        main_repo = model.SapnsRepo()
        main_repo.name = u'Main repo'
        main_repo.path = u''
        
        model.DBSession.add(main_repo)
        model.DBSession.flush()
        
        logger.info('Committing...')
        
        transaction.commit()
    except IntegrityError:
        print 'Warning, there was a problem adding your auth data, it may have already been added:'
        import traceback
        print traceback.format_exc()
        transaction.abort()
        print 'Continuing with bootstrapping...'
        

    # <websetup.bootstrap.after.auth>
