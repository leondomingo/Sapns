# -*- coding: utf-8 -*-

from sapns.lib.sapns.mongo import Mongo, SCHEDULED_TASKS, IN_PROGRESS, ERROR, SUCCESS, PENDING
from sapns.lib.sapns.mongo.scheduled_task import ScheduledTask
import datetime as dt
import logging


class Scheduler(object):

    def __init__(self, *args):
        self.mdb = Mongo().db
        self.args = args
        self.logger = logging.getLogger('Scheduler')

    def __call__(self):
        s = ScheduledTask()
        now_ = dt.datetime.now()
        self.logger.info(u'Looking for pending tasks...')
        for task in self.mdb[SCHEDULED_TASKS].find(dict(status=PENDING,
                                                        execution_time={'$lte': now_},
                                                        attempts={'$gt': 0})):

            task_id = task['_id']
            task = self.mdb[SCHEDULED_TASKS].find_one(dict(_id=task_id))
            if task['status'] != PENDING:
                continue

            self.logger.info(u'Task "%s" (%s) will be treated (%d attempt/s left)' % (task.get('description', task_id),
                                                                                      task_id,
                                                                                      task['attempts']))

            try:
                data = {'$set': dict(status=IN_PROGRESS,
                                     last_execution=dt.datetime.now()),
                        '$inc': dict(attempts=-1)}

                self.mdb[SCHEDULED_TASKS].update(dict(_id=task_id), data)

                s.execute(task_id)

                data = {'$set': dict(status=SUCCESS)}
                self.mdb[SCHEDULED_TASKS].update(dict(_id=task_id), data)

                # remove attachments of this task
                s.remove_attachments(task_id)

            except Exception, e:
                self.logger.error(e)

                if task['attempts'] == 1:
                    # task failed and it was the last time
                    data = {'$set': dict(status=ERROR, error_message=str(e))}

                    # remove attachments of this task
                    s.remove_attachments(task_id)

                else:
                    data = {'$set': dict(status=PENDING)}

                self.mdb[SCHEDULED_TASKS].update(dict(_id=task_id), data)
