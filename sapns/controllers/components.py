# -*- coding: utf-8 -*-

from pylons.i18n import ugettext as _
from sapns.lib.base import BaseController
from sapns.lib.sapns.util import get_template
from tg import expose, require, predicates as p_
import tg
import logging

class ComponentsController(BaseController):

    @expose('json')
    @require(p_.not_anonymous())
    def grid(self, **kw):
        logger = logging.getLogger('.grid')
        try:
            tmpl = get_template('sapns/components/sapns.grid/sapns.grid.min.js')
    
            content = tmpl.render(tg=tg, _=_,).encode('utf-8')
    
            return dict(status=True, content=content)
    
        except Exception, e:
            logger.error(e)
            return dict(status=False)

    @expose('json')
    @require(p_.not_anonymous())
    def selector(self, **kw):
        logger = logging.getLogger('.selector')
        try:
            tmpl = get_template('sapns/components/sapns.selector.min.js')
    
            content = tmpl.render(tg=tg, _=_,).encode('utf-8')
    
            return dict(status=True, content=content)
    
        except Exception, e:
            logger.error(e)
            return dict(status=False)

    @expose('json')
    @require(p_.not_anonymous())
    def uploader(self, **kw):
        logger = logging.getLogger('.uploader')
        try:
            tmpl = get_template('sapns/components/sapns.uploader.min.js')
    
            content = tmpl.render(tg=tg, _=_,).encode('utf-8')
    
            return dict(status=True, content=content)
    
        except Exception, e:
            logger.error(e)
            return dict(status=False)
