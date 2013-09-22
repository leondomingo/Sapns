# -*- coding: utf-8 -*-

from pylons.i18n import ugettext as _
from sapns.lib.base import BaseController
from sapns.lib.sapns.util import get_template
from tg import expose, require, response, predicates as p_
import tg
import logging
import os.path


class ComponentsController(BaseController):

    def _get_content(self, tmpl, **kw):
        tmpl = get_template(tmpl)
        return tmpl.render(tg=tg, _=_, **kw).encode('utf-8')

    @expose('text/plain')
    @require(p_.not_anonymous())
    def grid(self, **kw):
        logger = logging.getLogger('ComponentsController.grid')
        try:
            if kw.get('min', '') == '0':
                tmpl = 'sapns/components/sapns.grid/sapns.grid.js'

            else:
                tmpl = 'sapns/components/sapns.grid/sapns.grid.min.js'

            return self._get_content(tmpl)

        except Exception, e:
            logger.error(e)
            return ''

    @expose('text/plain')
    @require(p_.not_anonymous())
    def selector(self, **kw):
        logger = logging.getLogger('ComponentsController.selector')
        try:
            if kw.get('min', '') == '0':
                tmpl = 'sapns/components/sapns.selector/sapns.selector.js'

            else:
                tmpl = 'sapns/components/sapns.selector/sapns.selector.min.js'

            return self._get_content(tmpl)

        except Exception, e:
            logger.error(e)
            return ''

    @expose('text/plain')
    @require(p_.not_anonymous())
    def uploader(self, **kw):
        logger = logging.getLogger('ComponentsController.uploader')
        try:
            if kw.get('min', '') == '0':
                tmpl = 'sapns/components/sapns.uploader/sapns.uploader.js'
            else:
                tmpl = 'sapns/components/sapns.uploader/sapns.uploader.min.js'

            return self._get_content(tmpl)

        except Exception, e:
            logger.error(e)
            return ''

    @expose()
    @require(p_.not_anonymous())
    def load(self, **kw):
        logger = logging.getLogger('ComponentsController.load')
        try:
            tmpl = kw['tmpl']
            if tmpl == '_grid':
                tmpl = 'sapns/components/sapns.grid/sapns.grid.js'
                kw['min'] = 1

            elif tmpl == '_selector':
                tmpl = 'sapns/components/sapns.selector/sapns.selector.js'
                kw['min'] = 1

            elif tmpl == '_uploader':
                tmpl = 'sapns/components/sapns.uploader/sapns.uploader.js'
                kw['min'] = 1

            content = self._get_content(tmpl)

            # which extension?
            _name, ext = os.path.splitext(tmpl)

            if ext == '.js' and kw.get('min'):
                try:
                    from slimit import minify
                    content = minify(content, mangle=True)

                    response.content_type = 'text/javascript'

                except ImportError:
                    pass

            elif ext == '.scss':
                try:
                    from scss import Scss
                    css = Scss()
                    content = css.compile(content)

                    response.content_type = 'text/css'

                except ImportError:
                    content = '/*pyScss is not installed*/'

            else:
                response.content_type = 'text/plain'

            return content

        except Exception, e:
            logger.error(e)
            return ''
