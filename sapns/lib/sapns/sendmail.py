# -*- coding: utf-8 -*-

from tg import config
import logging
from sapns.lib.sapns.mongo.scheduled_task import ScheduledTask

class ESendMail(Exception):
    pass

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
          from_          {} (optional=<app.mailsender settings>)
          reply_to       <str> (opcional)
          files          [(<file_name>, <file-like object>), ...] (optional=[])
        """

        # collecting task data
        subject      = kw.get('subject')
        message_txt  = kw.get('message_txt')
        message_html = kw.get('message_html')

        if 'subject' not in kw:
            raise ESendMail('No subject has been specified')

        if 'message_txt' not in kw and 'message_html' not in kw:
            raise ESendMail('No message has been specified')

        if 'to' not in kw or len(kw['to']) == 0:
            raise ESendMail('No receivers have been specified')            

        # to
        to_ = []
        for email, name in kw['to']:
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

        data['from'] = kw.get('from_', from_default)

        # reply_to
        reply_to = kw.get('reply_to')
        if reply_to:
            data['from'].update(reply_to=reply_to)

        task_name = kw.get('task_name', 'Mail send')
        self.logger.info(u'Creating task "{0}"'.format(task_name))

        s = ScheduledTask()
        kw['description'] = task_name
        kw['executable'] = kw.get('sender', 'sapns.lib.sapns.mailsender.MailSender')
        kw.setdefault('delay', 1)
        kw['data'] = data

        task_id = s.register_task(**kw)
        s.attach_files(task_id, kw.get('files', []))


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
