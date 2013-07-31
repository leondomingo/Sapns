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

    def __init__(self):
        self.logger = logging.getLogger('MailSender')

    def __call__(self, **kw):

        # scheduled task
        task = dbs.query(SapnsScheduledTask).get(kw['stask_id'])

        # from / smtp connection
        from_address = config.get(self.APP_MAILSENDER__MAIL)
        from_name    = config.get(self.APP_MAILSENDER__NAME)
        reply_to = None
        if kw.get('from'):
            from_ = (kw['from'].get('address', from_address).encode('utf-8'),
                     kw['from'].get('name', from_name).encode('utf-8'),)

            # smtp
            server   = kw['from'].get('smtp', config.get(self.APP_MAILSENDER__SMTP))
            login    = kw['from'].get('login', config.get(self.APP_MAILSENDER__LOGIN))
            password = kw['from'].get('password', config.get(self.APP_MAILSENDER__PASSWORD))
            reply_to = kw['from'].get('reply_to')

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
        if kw.get('to'):
            to_ = _dst_list(kw['to'])

        cc = []
        if kw.get('cc'):
            cc = _dst_list(kw['cc'])

        bcc = []
        if kw.get('bcc'):
            bcc = _dst_list(kw['bcc'])

        # collect attachments
        files = []
        files_remove = []
        try:
            for doc in SapnsDoc.get_docs('sp_scheduled_tasks', task.scheduledtask_id):
                f = open(os.path.join(doc.repo.abs_path(), doc.filename).encode('utf-8'), 'rb')
                fn = (u'%s.%s' % (doc.title, doc.docformat.extension)).encode('utf-8')
                fn = re.sub(r'[^a-z0-9_\-\.]', '_', fn.lower())
                files.append((f, fn,))

                if kw.get('remove_attachments'):
                    files_remove.append(doc.doc_id)

            html_message = kw['message'].get('html')
            if html_message:
                html_message = html_message.encode('utf-8')

            send_mail(from_, to_, kw['subject'].encode('utf-8'),
                      kw['message']['text'].encode('utf-8'),
                      server, login, password, files=files,
                      html=html_message, cc=cc, bcc=bcc, reply_to=reply_to)

            # remove attachments
            for id_doc in files_remove:
                SapnsDoc.delete_doc(id_doc)

        finally:
            for f, _ in files:
                f.close()
