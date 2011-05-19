# -*- coding: utf-8 -*-
"""Messages management controller"""

# turbogears imports
from tg import expose, url, config, redirect, request

# third party imports
from pylons.i18n import ugettext as _
from pylons.i18n import lazy_ugettext as l_
from repoze.what import authorize

# project specific imports
from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs

import logging
from sapns.model.sapnsmodel import SapnsUser

__all__ = ['ShortcutsController']

class MessagesController(BaseController):
    
    allow_only = authorize.not_anonymous()
    
    @expose('messages/index.html')
    def index(self):
        
        user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
        messages = user.get_messages()
        
        return dict(page='messages', came_from='/dashboard', messages=messages)