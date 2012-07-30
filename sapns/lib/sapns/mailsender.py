# -*- coding: utf-8 -*-

from neptuno.sendmail import send_mail
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsScheduledTask, SapnsDoc
from tg import config
import logging
import os.path
import re

class MailSender(object):
    
    def __init__(self, **kw):
        self.logger = logging.getLogger('MailSender')
        self.params = kw
        
    def __call__(self):
        
        # scheduled task
        task = dbs.query(SapnsScheduledTask).get(self.params['stask_id'])
        
        # from
        from_ = (self.params['from']['address'].encode('utf-8'), 
                 self.params['from']['name'].encode('utf-8'),)
        
        def _dst_list(list_):
            r = []
            for dst in list_:
                r.append((dst['address'].encode('utf-8'), dst.get('name', u'').encode('utf-8'),))
                
            return r
        
        # to, cc, bcc
        to_ = []
        if self.params.get('to'):
            to_ = _dst_list(self.params['to'])
            
        cc = []
        if self.params.get('cc'):
            cc = _dst_list(self.params['cc'])
        
        bcc = []
        if self.params.get('bcc'):
            bcc = _dst_list(self.params['bcc'])
            
        # smtp connection
        server = self.params['from'].get('smtp', config.get('app.mailsender.smtp'))
        login = self.params['from'].get('login', config.get('app.mailsender.login'))
        password = self.params['from'].get('password', config.get('app.mailsender.password'))
        
        # collect attachments
        try:
            files = []
            for doc in SapnsDoc.get_docs('sp_scheduled_tasks', task.scheduledtask_id):
                f = open(os.path.join(doc.repo.abs_path(), doc.filename).encode('utf-8'), 'rb')
                fn = (u'%s.%s' % (doc.title, doc.docformat.extension)).encode('utf-8')
                fn = re.sub(r'[^a-z0-9_\-\.]', '_', fn.lower())
                files.append((f, fn,))
                
            send_mail(from_, to_, self.params['subject'], self.params['message']['text'],
                      server, login, password, files=files, 
                      html=self.params['message'].get('html'),
                      cc=cc, bcc=bcc)
            
        finally:
            for f, _ in files:
                f.close()