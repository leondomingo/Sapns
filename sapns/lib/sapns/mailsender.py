# -*- coding: utf-8 -*-

from cStringIO import StringIO
from neptuno.sendmail import send_mail
from sapns.lib.sapns.mongo import Mongo, SCHEDULED_TASKS, SCHEDULED_TASKS_ATTACHMENTS
from tg import config
import gridfs
import re
import logging


class MailSender(object):

    APP_MAILSENDER__MAIL     = 'app.mailsender.mail'
    APP_MAILSENDER__NAME     = 'app.mailsender.name'
    APP_MAILSENDER__LOGIN    = 'app.mailsender.login'
    APP_MAILSENDER__PASSWORD = 'app.mailsender.password'
    APP_MAILSENDER__SMTP     = 'app.mailsender.smtp'

    def __init__(self):
        self.logger = logging.getLogger('MailSender')
        self.mdb = Mongo().db
        self.fs = gridfs.GridFS(self.mdb, collection=SCHEDULED_TASKS_ATTACHMENTS)

    def __call__(self, **kw):

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
        task = self.mdb[SCHEDULED_TASKS].find_one(dict(_id=kw['task_id']))
        attachments = task.get('attachments')
        if attachments:
            names = task.get('attachments_names')

            for attachment_id, attachment_name in zip(attachments, names):
                f = StringIO(self.fs.get(attachment_id).read())
                fn = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', attachment_name.encode('utf-8'))
                files.append((f, fn))

                # delete attachment from GridFS (mongodb)
                self.fs.delete(attachment_id)

        html_message = kw['message'].get('html')
        if html_message:
            html_message = html_message.encode('utf-8')

        send_mail(from_, to_, kw['subject'].encode('utf-8'),
                  kw['message']['text'].encode('utf-8'),
                  server, login, password, files=files,
                  html=html_message, cc=cc, bcc=bcc, reply_to=reply_to)
