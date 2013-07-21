# -*- coding: utf-8 -*-

from neptuno.sendmail import send_mail
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsScheduledTask, SapnsDoc
from tg import config
import logging
import os.path
import re


class MailSender(object):

    APP_MAILSENDER__MAIL     = 'app.mailsender.mail'
    APP_MAILSENDER__NAME     = 'app.mailsender.name'
    APP_MAILSENDER__LOGIN    = 'app.mailsender.login'
    APP_MAILSENDER__PASSWORD = 'app.mailsender.password'
    APP_MAILSENDER__SMTP     = 'app.mailsender.smtp'

    def __init__(self, **kw):
        self.logger = logging.getLogger('MailSender')
        self.params = kw

    def __call__(self):

        # scheduled task
        task = dbs.query(SapnsScheduledTask).get(self.params['stask_id'])

        # from / smtp connection
        from_address = config.get(self.APP_MAILSENDER__MAIL)
        from_name    = config.get(self.APP_MAILSENDER__NAME)
        reply_to = None
        if self.params.get('from'):
            from_ = (self.params['from'].get('address', from_address).encode('utf-8'),
                     self.params['from'].get('name', from_name).encode('utf-8'),)

            # smtp
            server   = self.params['from'].get('smtp', config.get(self.APP_MAILSENDER__SMTP))
            login    = self.params['from'].get('login', config.get(self.APP_MAILSENDER__LOGIN))
            password = self.params['from'].get('password', config.get(self.APP_MAILSENDER__PASSWORD))
            reply_to = self.params['from'].get('reply_to')

        else:
            from_ = (from_address, from_name,)

            # smtp
            server   = config.get(self.APP_MAILSENDER__SMTP)
            login    = config.get(self.APP_MAILSENDER__LOGIN)
            password = config.get(self.APP_MAILSENDER__PASSWORD)

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

        # collect attachments
        files = []
        files_remove = []
        try:
            for doc in SapnsDoc.get_docs('sp_scheduled_tasks', task.scheduledtask_id):
                f = open(os.path.join(doc.repo.abs_path(), doc.filename).encode('utf-8'), 'rb')
                fn = (u'%s.%s' % (doc.title, doc.docformat.extension)).encode('utf-8')
                fn = re.sub(r'[^a-z0-9_\-\.]', '_', fn.lower())
                files.append((f, fn,))

                if self.params.get('remove_attachments'):
                    files_remove.append(doc.doc_id)

            send_mail(from_, to_, self.params['subject'].encode('utf-8'),
                      self.params['message']['text'].encode('utf-8'),
                      server, login, password, files=files,
                      html=self.params['message'].get('html').encode('utf-8'),
                      cc=cc, bcc=bcc, reply_to=reply_to)

            # remove attachments
            for id_doc in files_remove:
                SapnsDoc.delete_doc(id_doc)

        finally:
            for f, _ in files:
                f.close()
