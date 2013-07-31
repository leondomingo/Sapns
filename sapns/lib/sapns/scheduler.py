# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsScheduledTask
from sqlalchemy.sql.expression import and_, not_
from tg import config
import datetime as dt
import logging
import os
import transaction


class Scheduler(object):

    def __init__(self):
        self.logger = logging.getLogger('Scheduler')

    def __call__(self):

        now = dt.datetime.now()
        limit_tasks = config.get('app.scheduler.limit_task')
        lock_path = config.get('app.scheduler.lock_path', '/tmp/sapns_scheduler.lock')

        if os.path.exists(lock_path):
            exit(1)

        f = open(lock_path, 'wb')
        try:
            for id_stask in dbs.query(SapnsScheduledTask.scheduledtask_id).\
                    filter(and_(SapnsScheduledTask.active,
                                not_(SapnsScheduledTask.executed),
                                not_(SapnsScheduledTask.in_progress),
                                )).\
                    limit(limit_tasks):

                transaction.begin()
                try:
                    stask = dbs.query(SapnsScheduledTask).get(id_stask)

                    execute = False
                    mark_as_executed = False

                    if stask.task_date and stask.task_date <= now.date():
                        # scheduled for a particular date and time
                        if stask.task_time <= now.time():
                            execute = True
                            mark_as_executed = True

                    elif not stask.task_date and stask.task_time and stask.task_time <= now.time():
                        # scheduled...
                        #  ...for a particular time in a particular day of the week, or
                        #  ...for a particular day of the week every "period" minutes

                        if not stask.period and (stask.last_execution or dt.datetime(1970, 1, 1)).date() == now.date():
                            continue

                        wd = now.date().weekday()

                        # monday
                        if wd == 0 and stask.monday:
                            execute = True
                            mark_as_executed = True

                        # tuesday
                        elif wd == 1 and stask.tuesday:
                            execute = True
                            mark_as_executed = True

                        # wednesday
                        elif wd == 2 and stask.wednesday:
                            execute = True
                            mark_as_executed = True

                        # thursday
                        elif wd == 3 and stask.thursday:
                            execute = True
                            mark_as_executed = True

                        # friday
                        elif wd == 4 and stask.friday:
                            execute = True
                            mark_as_executed = True

                        # saturday
                        elif wd == 5 and stask.saturday:
                            execute = True
                            mark_as_executed = True

                        # sunday
                        elif wd == 6 and stask.sunday:
                            execute = True
                            mark_as_executed = True

                        mark_as_executed = mark_as_executed and stask.period

                    if execute:
                        self.logger.info(u'%s (%s)' % (stask.task_name, stask.executable))

                        # task "in progress"
                        stask.in_progress = True
                        dbs.add(stask)
                        transaction.commit()

                        try:
                            error = False
                            try:
                                stask_ = dbs.query(SapnsScheduledTask).get(id_stask)
                                stask_.execute()

                            except Exception, e:
                                self.logger.error(e)
                                error = True

                                if stask_.max_attempts:
                                    stask_.attempts += 1

                                    if stask_.max_attempts == stask_.attempts:

                                        if stask_.task_date and stask_.task_time:
                                            mark_as_executed = True

                                        elif not stask_.task_date and stask_.task_time and not stask_.period:
                                            stask_.attempts = 0
                                            stask_.last_execution = now

                                        elif stask_.period:
                                            stask_.reschedule(stask_.period)

                                    else:
                                        mark_as_executed = False

                            # update task
                            if not error:
                                if mark_as_executed or stask_.just_one_time:
                                    stask_.executed = True

                                stask_.last_execution = dt.datetime.now()

                                # re-schedule in "period" minutes
                                if stask_.period or 0:
                                    stask_.attempts = 0
                                    stask_.reschedule(stask_.period)

                        finally:
                            stask_.in_progress = False
                            dbs.add(stask_)
                            dbs.flush()
                            transaction.commit()

                finally:
                    transaction.abort()
        finally:
            f.close()
            if os.path.exists(lock_path):
                os.remove(lock_path)
