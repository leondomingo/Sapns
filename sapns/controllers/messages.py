# -*- coding: utf-8 -*-
"""Messages management controller"""

# turbogears imports
from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser
from tg import expose, request, predicates

__all__ = ['ShortcutsController']

class MessagesController(BaseController):
    
    allow_only = predicates.not_anonymous()
    
    @expose('sapns/messages/index.html')
    def index(self):
        
        user = dbs.query(SapnsUser).get(request.identity['user'].user_id)
        messages = user.get_messages()
        
        return dict(page='messages', came_from='/dashboard', messages=messages)