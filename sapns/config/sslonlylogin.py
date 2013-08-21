# -*- coding: utf-8 -*-

class SSLOnlyLoginMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if environ['wsgi.url_scheme'] != 'https':
            environ['HTTP_HTTPS'] = 'on'
            environ['wsgi.url_scheme'] = 'https'

        return self.app(environ, start_response)
