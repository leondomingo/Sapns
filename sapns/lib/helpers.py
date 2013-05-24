# -*- coding: utf-8 -*-

"""WebHelpers used in sapns."""

from webhelpers import date, feedgenerator, html, number, misc, text
from tg import predicates, config
from sapns.util import ROLE_MANAGERS, datetostr

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
