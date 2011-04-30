# -*- coding: utf-8 -*-
"""Users management controller"""

# turbogears imports
from tg import expose, url, config, redirect

# third party imports
from pylons.i18n import ugettext as _
from pylons.i18n import lazy_ugettext as l_
from repoze.what import authorize

# project specific imports
from sapns.lib.base import BaseController
from sapns.model import DBSession

import logging
from sapns.model.sapnsmodel import SapnsUser 
from neptuno.dataset import DataSet

__all__ = ['ShortcutsController']

class ShortcutsController(BaseController):
    
    allow_only = authorize.not_anonymous()
    
    @expose('shortcuts/edit.html')
    def edit(self, id=None, **params):
        came_from = params.get('came_from', '/')
        page = _('Shorcuts editing')
        
        return dict(page=page, came_from=came_from)
    
    @expose()
    def save(self, id=None, **params):
        came_from = params.get('came_from', '/')
        redirect(url(came_from))
    
    @expose('json')
    def delete(self, id=None, **params):
        #came_from = params.get('came_from', '/')
        return dict(status=True)
    
    @expose('json')
    def bookmark(self, id=None, **params):
        #came_from = params.get('came_from', '/')
        return dict(status=True)
    
    