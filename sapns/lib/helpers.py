# -*- coding: utf-8 -*-

"""WebHelpers used in sapns."""

from webhelpers import date, feedgenerator, html, number, misc, text
from pylons.i18n import ugettext as _
from tg import predicates, config
import tg
from sapns.util import ROLE_MANAGERS, datetostr, get_template
import os.path

def is_manager():
    return predicates.in_group(ROLE_MANAGERS)

def allowed(permission_name):
    return predicates.has_permission(permission_name)

def root_folder():
    return config.get('app.root_folder')

def today():
    import datetime as dt
    return datetostr(dt.date.today())

def url2(url):
    import urllib
    
    base_url = config.get('app.url')
    if not base_url:
        return url
    
    else:
        return urllib.basejoin(base_url, url)

def load(tmpl_name, minify=True, **kw):

    tmpl = get_template(tmpl_name)
    content = tmpl.render(tg=tg, _=_, **kw)

    _name, ext = os.path.splitext(tmpl_name)

    if ext == '.js' and minify:
        try:
            from slimit import minify
            content = minify(content, mangle=True)

        except ImportError:
            pass

    return content
