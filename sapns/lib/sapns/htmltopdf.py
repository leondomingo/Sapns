# -*- coding: utf-8 -*-

from webob import Request
from sapns.lib.sapns.util import topdf
import logging

class HtmlToPdfMiddleware(object):

    def __init__(self, application, config):
        self.application = application
        
    def __call__(self, environ, start_response):
        logger = logging.getLogger('HtmlToPdfMiddleware.__call__')
        request = Request(environ)
        response = request.get_response(self.application)
        logger.info(environ['HTTP_HOST'])
        if environ.has_key('to_pdf'):
            response.content_type = 'application/pdf'
            response.headerlist.append(("content-disposition",
                                        "attachment; filename=%s" % request.environ['to_pdf']))
            response.body = topdf(response.body)
        
        return response(environ, start_response)
    
def url2(url):
    from tg import config
    import urllib
    
    base_url = config.get('app.url')
    if not base_url:
        return url
    
    else:
        return urllib.basejoin(base_url, url)