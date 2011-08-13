# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs
from pylons.i18n import ugettext as _
# more imports here...
#from pylons.templating import render_jinja2
from sapns.lib.sapns.util import update_metadata, create_data_exploration
from sapns.model import SapnsAction, SapnsClass, SapnsRole

import logging

class SapnsInit(object):

#    def render(self, template, extra_vars):
#        return render_jinja2(template, extra_vars=extra_vars)

    def privilege_actions(self):
        
        logger = logging.getLogger('SapnsInit.privilege_actions')
        try:
            logger.info('Creating action "Privileges" for "sp_roles"')
            role_p = SapnsAction()
            role_p.name = _('Privileges')
            role_p.class_id = SapnsClass.by_name('sp_roles')
            role_p.type = SapnsAction.TYPE_PROCESS
            role_p.url = u'/dashboard/privileges/roles/'
            
            dbs.add(role_p)
            dbs.flush()
            
            logger.info('Creating action "Privileges" for "sp_users"')
            users_p = SapnsAction()
            users_p.name = _('Privileges')
            users_p.class_id = SapnsClass.by_name('sp_users')
            users_p.type = SapnsAction.TYPE_PROCESS
            users_p.url = u'/dashboard/privileges/users/'
            
            dbs.add(users_p)
            dbs.flush()
            
            managers = SapnsRole.by_name(u'managers')
            #managers = SapnsRole()
            managers.add_act_privilege(role_p.action_id)
            managers.add_act_privilege(users_p.action_id)
        
        except Exception, e:
            logger.error(e)
            raise
    
    def __call__(self):
        #update_metadata()
        #create_data_exploration()
        self.privilege_actions()
        
        dbs.commit()

update = SapnsInit()