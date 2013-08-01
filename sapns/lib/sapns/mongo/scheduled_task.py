# -*- coding: utf-8 -*-

from sapns.lib.sapns.mongo import Mongo, PENDING, SCHEDULED_TASKS, SCHEDULED_TASKS_ATTACHMENTS
from bson.objectid import ObjectId
import datetime as dt
import logging
import gridfs


class ScheduledTask(object):

    def __init__(self):
        self.logger = logging.getLogger('ScheduledTask')
        self.mdb = Mongo().db
        self.fs = gridfs.GridFS(self.mdb, collection=SCHEDULED_TASKS_ATTACHMENTS)

    def register_task(self, **kw):
        """Create a new task"""

        task = dict(data=kw.get('data', {}),
                    executable=kw['executable'],
                    status=PENDING,
                    execution_time=kw.get('execution_time', dt.datetime.now()),
                    description=kw.get('description'),
                    attempts=kw.get('max_attempts', 3),
                    max_attempts=kw.get('max_attempts', 3),
                    attachments=[],
                    attachments_names=[],
                    )

        delay = kw.get('delay')
        if delay:
            task['execution_time'] = dt.datetime.now() + dt.timedelta(seconds=delay*60)

        task_id = self.mdb[SCHEDULED_TASKS].insert(task)
        self.logger.info(u'Task "%s" (%s) has been registered' % (kw.get('description', task_id), task_id))

        return task_id

    def attach_files(self, task_id, files):
        """Attach files to a task"""
        task_id = ObjectId(task_id)
        for file_name, f in files:
            if hasattr(f, 'getvalue'):
                # cStringIO.StringIO
                file_data = f.getvalue()
            else:
                file_data = f.file

            file_id = self.fs.put(file_data)

            self.mdb[SCHEDULED_TASKS].update(dict(_id=task_id),
                                             {'$push': dict(attachments=file_id,
                                                            attachments_names=file_name)})

    def remove_attachments(self, task_id):
        """Remove all attachment of a task, if there's any"""
        task_id = ObjectId(task_id)
        task = self.mdb[SCHEDULED_TASKS].find_one(dict(_id=task_id))
        for file_id in task.get('attachments', []):
            self.fs.delete(file_id)

    def task_status(self, task_id):
        task = self.mdb[SCHEDULED_TASKS].find_one(dict(_id=ObjectId(task_id)))

        return task['status'], task.get('error_message')

    def execute(self, task_id):
        """Execute a task"""

        task_id = ObjectId(task_id)
        task = self.mdb[SCHEDULED_TASKS].find_one(dict(_id=task_id))

        self.logger.info(u'Executing task "%s" (%s)' % (task.get('description', task_id), task_id))

        executable = task['executable'].split('.')
        pkg = '.'.join(executable[:-1])
        cls = executable[-1]

        m = __import__(pkg, fromlist=[cls])
        func = getattr(m, cls)
        if isinstance(func, type):
            func = func()

        task['data'].update(task_id=task_id)
        func(**task['data'])

