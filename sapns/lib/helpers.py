# -*- coding: utf-8 -*-

"""WebHelpers used in sapns."""

from webhelpers import date, feedgenerator, html, number, misc, text
from tg import predicates

def url2(url):
    from tg import config
    import urllib
    
    base_url = config.get('app.url')
    if not base_url:
        return url
    
    else:
        return urllib.basejoin(base_url, url)