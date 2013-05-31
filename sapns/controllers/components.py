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
        logger = logging.getLogger('ComponentsController.grid')
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
        logger = logging.getLogger('ComponentsController.selector')
        try:
            tmpl = get_template('sapns/components/sapns.selector/sapns.selector.min.js')
    
            content = tmpl.render(tg=tg, _=_,).encode('utf-8')
    
            return dict(status=True, content=content)
    
        except Exception, e:
            logger.error(e)
            return dict(status=False)

    @expose('json')
    @require(p_.not_anonymous())
    def uploader(self, **kw):
        logger = logging.getLogger('ComponentsController.uploader')
        try:
            tmpl = get_template('sapns/components/sapns.uploader/sapns.uploader.min.js')
    
            content = tmpl.render(tg=tg, _=_,).encode('utf-8')
    
            return dict(status=True, content=content)
    
        except Exception, e:
            logger.error(e)
            return dict(status=False)

    @expose('json')
    @require(p_.not_anonymous())
    def load(self, tmpl, **kw):
        try:
            from slimit import minify
        except ImportError:
            def minify(text, **kwargs):
                return text

        logger = logging.getLogger('ComponentsController.uploader')
        try:
            tmpl_ = get_template(tmpl.replace('$', '/').replace('__', '.'))
            content = tmpl_.render(tg=tg, _=_,).encode('utf-8')

            if kw.get('min'):
                content = minify(content, mangle=True)
        
            return dict(status=True, content=content)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False)
