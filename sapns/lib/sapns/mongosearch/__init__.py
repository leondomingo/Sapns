# -*- coding: utf-8 -*-

from sapns.lib.sapns.mongo import Mongo
import re
import logging
import datetime as dt

class SearchMongo(object):

    def __init__(self, db, coll, cols, datetime_format=None):
        self.db = db
        self.coll = coll
        self.cols = dict(cols)
        self.logger = logging.getLogger('SearchMongo')
        self.datetime_format = datetime_format

    def no_accents(self, text):
        
        result = text.encode('utf-8')
        result = re.sub(r'(a|á|à|ä)', '(a|á|à|ä)', result)
        result = re.sub(r'(e|é|è|ë)', '(e|é|è|ë)', result)
        result = re.sub(r'(i|í|ì|ï)', '(i|í|ì|ï)', result)
        result = re.sub(r'(o|ó|ò|ö)', '(o|ó|ò|ö)', result)
        result = re.sub(r'(u|ú|ù|ü)', '(u|ú|ù|ü)', result)
        
        return result.decode('utf-8')

    def _datetime_re(self):
        sr = self.datetime_format.\
            replace('%d', r'(?P<day>\d{1,2})').\
            replace('%m', r'(?P<month>\d{1,2})').\
            replace('%Y', r'(?P<year>\d{4})').\
            replace('%H', r'(?P<hour>\d{1,2})').\
            replace('%M', r'(?P<minute>\d{2})').\
            replace('%S', r'(?P<second>\d{2})')

        sr = '^%s$' % sr

        return re.compile(sr)

    def _get_datetime(self, value):
        m = re.search(self._datetime_re(), value)
        if m:
            day = int(m.group('day'))
            month = int(m.group('month'))
            year = int(m.group('year'))
            hour = int(m.group('hour') or 0)
            minute = int(m.group('minute') or 0)
            second = int(m.group('second') or 0)

            return dt.datetime(year, month, day, hour, minute, second)

        raise ValueError

    def _process_query(self, q):
        s = {}
        if q:
            if isinstance(q, str):
                q = q.decode('utf-8')

            # TODO: process query string
            for item in q.split(','):
                item = item.strip()
                self.logger.info(item)

                m = re.search(r'^([\w\.]*)\s*(<>|<=|>=|==|=|<|>|#|!)(.+)', item)
                if m:
                    self.logger.info(m.groups())

                    field_name = m.group(1)
                    field_type = self.cols.get(field_name, 'str')
                    operator = m.group(2)
                    value = m.group(3)

                    # = (equal)
                    if operator == '=':
                        if field_type == 'str':
                            s[field_name] = re.compile(self.no_accents(value), re.I)

                        elif field_type == 'int':
                            try:
                                s[field_name] = int(value)
                            except ValueError:
                                pass

                        elif field_type == 'float':
                            try:
                                s[field_name] = float(value)
                            except ValueError:
                                pass

                        elif field_type == 'datetime':
                            try:
                                s[field_name] = self._get_datetime(value)
                            except ValueError:
                                pass

                    # <> (not equal)
                    elif operator == '<>':
                        if field_type == 'str':
                            s[field_name] = { '$not': re.compile(self.no_accents(value), re.I) }

                        elif field_type == 'int':
                            try:
                                s[field_name] = { '$not': int(value) }
                            except ValueError:
                                pass

                        elif field_type == 'float':
                            try:
                                s[field_name] = { '$not': float(value) }
                            except ValueError:
                                pass

                    elif operator == '==':
                        s[field_name] = re.compile(value, re.I)

                    # < (less than)
                    elif operator == '<':
                        if field_type == 'int':
                            try:
                                s[field_name] = { '$lt': int(value) }
                            except ValueError:
                                pass

                        elif field_type == 'datetime':
                            try:
                                s[field_name] = { '$lt': self._get_datetime(value) }
                            except ValueError:
                                pass

                    # <= (less than or equal)
                    elif operator == '<=':
                        if field_type == 'int':
                            try:
                                s[field_name] = { '$lte': int(value) }
                            except ValueError:
                                pass

                        elif field_type == 'datetime':
                            try:
                                s[field_name] = { '$lte': self._get_datetime(value) }
                            except ValueError:
                                pass

                    # > (greater than)
                    elif operator == '>':
                        if field_type == 'int':
                            try:
                                s[field_name] = { '$gt': int(value) }
                            except ValueError:
                                pass

                        elif field_type == 'datetime':
                            try:
                                s[field_name] = { '$gt': self._get_datetime(value) }
                            except ValueError:
                                pass

                    # >= (greater than or equal)
                    elif operator == '>=':
                        if field_type == 'int':
                            try:
                                s[field_name] = { '$gte': int(value) }
                            except ValueError:
                                pass

                        elif field_type == 'datetime':
                            try:
                                s[field_name] = { '$gte': self._get_datetime(value) }
                            except ValueError:
                                pass

        return s

    def __call__(self, q=None, rp=100, offset=0):

        search = self._process_query(q)
        self.logger.info(search)
        
        result = []
        for row in self.db[self.coll].find(search).limit(rp).skip(offset):
            result.append(row)

        return result

class Test(object):

    def __init__(self, *args):
        self.args = args

    def __call__(self):
        s = SearchMongo(Mongo().db, 'access',
                        [('what', 'str'), ('who.id', 'int'), ('when', 'datetime')],
                        datetime_format=r'%d/%m/%Y(\s+%H)?(:%M)?(:%S)?')

        print ','.join(self.args)
        for r in s(q=','.join(self.args)):
            print r
