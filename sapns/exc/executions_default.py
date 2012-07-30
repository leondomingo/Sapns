# -*- coding: utf-8 -*-

# copy this file as "executions.py" to add your own "scripts"
EXECUTIONS = {
    # exc_id: (<pkg_name>, <func_name/excutable_class_name>,)
    'update': ('sapns.exc.update.update', 'Update',),
    'initsp': ('sapns.lib.sapns.initsp', 'InitSapns',),
    'scheduler': ('sapns.lib.sapns.scheduler', 'Scheduler'),
    'mailsender': ('sapns.lib.sapns.mailsender', 'MailSender'),
    # examples
    'example.test1': ('sapns.exc.example.example', 'test1'),
    'example.test2': ('sapns.exc.example.example', 'test2', (100, 200,), dict(three=300)),
    'example.Test': ('sapns.exc.example.example', 'Test', (101, 202,), dict(three=303)),
    # TODO: other executions here
}