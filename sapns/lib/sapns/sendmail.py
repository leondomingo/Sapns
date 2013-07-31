# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsScheduledTask, SapnsRepo, SapnsDoc, SapnsDocFormat
import datetime as dt
import simplejson as sj
import os
from tg import config
import logging


class SendMail(object):

    def __init__(self):
        self.logger = logging.getLogger('SendMail')

    def __call__(self, **kw):
        """
        IN
          task_name      <str> (optional='mail send')
          max_attempts   <int> (optional=3)
          sender         <str> (optional='sapns.lib.sapns.mailsender.MailSender')
          delay          <int> (opcional=1)
          subject        <str>
          message_txt    <str>
          message_html   <str> (opcional)
          to             [(<email>, <name>,), ...]
          from           {} (optional=<app.mailsender settings>)
          reply_to       <str> (opcional)
          files          [(<file_name>, <file-like object>] (optional=[])
        """

        # create "scheduled task" to send mail
        stask = SapnsScheduledTask()
        stask.active = True
        stask.task_name = kw.get('task_name', 'mail send')
        stask.max_attempts = int(kw.get('max_attempts', 3) or 3)

        # send mail after 1 minute
        delay = int(kw.get('delay', 1))
        momento = dt.datetime.now() + dt.timedelta(minutes=delay)

        stask.task_date = momento.date()
        stask.task_time = momento.time()
        stask.executable = kw.get('sender', 'sapns.lib.sapns.mailsender.MailSender')

        subject = kw.get('subject')
        message_txt = kw.get('message_txt')
        message_html = kw.get('message_html')

        # to
        to_ = []
        for email, name in kw.get('to'):
            to_.append(dict(address=email, name=name))

        # from
        from_default = dict(address=config.get('app.mailsender.mail'),
                            name=config.get('app.mailsender.name'),
                            login=config.get('app.mailsender.login'),
                            password=config.get('app.mailsender.password'),
                            smtp=config.get('app.mailsender.smtp'),
                            )

        data = dict(to=to_,
                    subject=subject,
                    message=dict(text=message_txt, html=message_html),
                    remove_attachments=True)

        data['from'] = kw.get('from', from_default)

        # reply_to
        reply_to = kw.get('reply_to')
        if reply_to:
            data['from'].update(reply_to=reply_to)

        stask.data = sj.dumps(data)

        dbs.add(stask)
        dbs.flush()

        # get the first "repo"
        repo = dbs.query(SapnsRepo).first()

        for file_name, f in kw.get('files', []):
            path = repo.get_new_path()

            # split "file_name" into "name" and "ext" (foo-bar.png => foo-bar, .png)
            name, ext = os.path.splitext(file_name)

            with open(path, 'wb') as f_:
                attch = SapnsDoc()
                attch.author_id = kw.get('user_id')
                attch.title = os.path.basename(file_name)
                attch.repo_id = repo.repo_id
                attch.filename = os.path.basename(path)
                attch.docformat_id = SapnsDocFormat.by_extension(ext).docformat_id

                dbs.add(attch)
                dbs.flush()

                attch.register('sp_scheduled_tasks', stask.scheduledtask_id)

                f.seek(0)
                f_.write(f.read())


def send_mail(**kwargs):
    """
    IN
      task_name      <str> (optional='mail send')
      max_attempts   <int> (optional=3)
      sender         <str> (optional='sapns.lib.sapns.mailsender.MailSender')
      delay          <int> (opcional=1)
      subject        <str>
      message_txt    <str>
      message_html   <str> (opcional)
      to             [(<email>, <name>,), ...]
      from           {} (optional=<app.mailsender settings>)
      reply_to       <str> (opcional)
      files          [(<file_name>, <file-like object>] (optional=[])
    """
    ms = SendMail()
    return ms(**kwargs)
