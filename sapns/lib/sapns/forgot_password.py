# -*- coding: utf-8 -*-

from jinja2 import Environment, PackageLoader
from neptuno.sendmail import send_mail
from sapns.lib.sapns.util import init_lang
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser
from sqlalchemy import or_, func
from tg import config
import hashlib as hl
import random

class EUserDoesNotExist(Exception):
    pass

class ForgotPassword(object):
    
    def __init__(self, username_or_email):
        
        #logger = logging.getLogger('ForgotPassword.__init__')
        
        self.u = dbs.query(SapnsUser).\
                filter(or_(func.upper(SapnsUser.user_name) == func.upper(username_or_email),
                           func.upper(SapnsUser.email_address) == func.upper(username_or_email),
                           )).\
                first()
                
        if not self.u:
            raise EUserDoesNotExist
            
        # generate a random password
        random.seed()
        s1 = hl.sha1('%6.6d' % random.randint(0, 999999))
        
        self.new_password = ''
        for c in s1.hexdigest()[:random.randint(10, 15)]:
            if random.randint(0, 1):
                self.new_password += c.upper()
                
            else:
                self.new_password += c
        
        self.u.password = self.new_password
        dbs.add(self.u)
        dbs.flush()
        
        self.dst = [(self.u.email_address.encode('utf-8'), self.u.user_name.encode('utf-8'),)]
            
        # e-mail settings
        self.remitente = (config.get('app.mailsender.e_mail'), config.get('app.mailsender.name'),)
        
        # get e-mail templates
        self.env = Environment(loader=PackageLoader('sapns', 'templates'))
        
    def __call__(self):
        
        lang = init_lang()
        
        vars_ = dict(display_name=self.u.display_name,
                     user_name=self.u.user_name,
                     new_password=self.new_password,
                     app_title=config.get('app.mailsender.name').decode('utf-8'),
                     )
        
        asunto = self.env.get_template('sapns/users/forgot_password/%s/subject.txt' % lang)
        asunto = asunto.render(**vars_).encode('utf-8')
        
        mensaje = self.env.get_template('sapns/users/forgot_password/%s/message.txt' % lang)
        mensaje = mensaje.render(**vars_).encode('utf-8')
        
        mensaje_html = self.env.get_template('sapns/users/forgot_password/%s/message.html' % lang)
        mensaje_html = mensaje_html.render(**vars_).encode('utf-8')
        
        email_login = config.get('app.mailsender.login')
        email_password = config.get('app.mailsender.password')
        
        # send e-mail
        send_mail(self.remitente, self.dst, asunto, mensaje,
                  config.get('app.mailsender.smtp'), email_login, email_password, 
                  html=mensaje_html)