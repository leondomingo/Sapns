# -*- coding: utf-8 -*-

from bson.objectid import ObjectId
from pylons.i18n import ugettext as _
from sapns.lib.sapns.util import strtodate as _strtodate
from sapns.lib.sapns.mongo import Mongo
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsAttribute, SapnsClass, SapnsPermission
from tg import config, request
import datetime as dt
import logging
import re
from copy import deepcopy
from zope.sqlalchemy import mark_changed
from sqlalchemy import and_

# might be anything except a number (0, 1, 2, ...) or # (sharp symbol)
COLLECTION_CHAR = 'c'


def get_view_name(name):
    return '{prefix}{name}'.format(prefix=config.get('views_prefix', '_view_'), name=name)


def get_query(view_id):

    logger = logging.getLogger('sapns.lib.sapns.views.get_query')

    mdb = Mongo().db

    view = {}
    if isinstance(view_id, (str, unicode,)):
        view_id = ObjectId(view_id)
        view = mdb.user_views.find_one(dict(_id=view_id))

    elif isinstance(view_id, dict):
        view = view_id

    elif isinstance(view_id, ObjectId):
        view = mdb.user_views.find_one(dict(_id=view_id))

    def _get_parent(alias):

        logger.debug(u'parent of "%s"' % alias)

        # alumnos
        parent_class = re.search(r'_(%s?)(\d+)$' % COLLECTION_CHAR, alias)
        collection = parent_class.group(1)
        attribute_id = int(parent_class.group(2))
        attribute_ = dbs.query(SapnsAttribute).get(attribute_id)

        class_ = re.search(r'^([a-z_]+)_', alias).group(1)

        if not collection:
            alias_ = alias.replace(class_, attribute_.class_.name)

        else:
            alias_ = alias.replace(class_, attribute_.related_class.name)

        alias_ = re.sub(r'_%s?%s$' % (COLLECTION_CHAR, attribute_id), '', alias_)

        if not re.search(r'_%s?\d+$' % COLLECTION_CHAR, alias_):
            alias_ = '{alias}_0'.format(alias=alias_)

        logger.debug((alias_, attribute_.name,))
        return alias_, attribute_.name

    columns = []
    filters = []
    relations = []
    relations_ = {}
    nagg_columns = []
    agg_columns = []

    _cmp = lambda x, y: cmp(x.get('order', 0), y.get('order', 0))
    attributes_list = sorted(view['attributes_detail'], cmp=_cmp) + view.get('advanced_filters', [])
    for attribute in attributes_list:

        logger.debug(attribute)

        if not relations_.get(attribute['class_alias']):
            relations_[attribute['class_alias']] = True

            base_table = re.search(r'^(\w+)_0$', attribute['class_alias'])
            if not base_table:
                parent_alias, parent_attribute = _get_parent(attribute['class_alias'])

                relations__ = []

                if re.search(r'\w+_%s\d+$' % COLLECTION_CHAR, attribute['class_alias']):
                    relations__.insert(0, u'LEFT JOIN %s %s ON %s.id = %s.%s' % (attribute['class_name'],
                                                                                 attribute['class_alias'],
                                                                                 parent_alias,
                                                                                 attribute['class_alias'],
                                                                                 parent_attribute))

                else:
                    relations__.insert(0, u'LEFT JOIN %s %s ON %s.id = %s.%s' % (attribute['class_name'],
                                                                                 attribute['class_alias'],
                                                                                 attribute['class_alias'],
                                                                                 parent_alias, parent_attribute,
                                                                                 ))

                end_ = False
                while not end_:
                    base = re.search(r'\w+_0', parent_alias)
                    if not base:
                        parent_alias_, parent_attribute_ = _get_parent(parent_alias)

                        parent_class = re.search(r'^([a-z_]+)_', parent_alias).group(1)

                        if not relations_.get(parent_alias):
                            relations_[parent_alias] = True
                            if re.search(r'\w+_%s\d+$' % COLLECTION_CHAR, parent_alias):
                                relations__.insert(0, u'LEFT JOIN %s %s ON %s.id = %s.%s' % (parent_class, parent_alias,
                                                                                             parent_alias_,
                                                                                             parent_alias,
                                                                                             parent_attribute_,
                                                                                             ))

                            else:
                                relations__.insert(0, u'LEFT JOIN %s %s ON %s.id = %s.%s' % (parent_class, parent_alias,
                                                                                             parent_alias,
                                                                                             parent_alias_,
                                                                                             parent_attribute_,
                                                                                             ))

                        parent_alias = parent_alias_

                    else:
                        end_ = True

                relations += relations__

        if not attribute.get('is_filter'):
            col_title = u'"%s"' % attribute['title']
            columns.append(u'{expression} AS "{title}"'.format(expression=attribute['expression'],
                                                               title=attribute['title']))
        else:
            if not attribute.get('variable'):
                filters.append(attribute['expression'])

            else:
                # these filters will be applied when the user ask for the view
                logger.debug(u'variable filter=%s' % attribute['value'])
                columns.append(u'%s AS "id_%s"' % (attribute['attr'], attribute['attr']))
                nagg_columns.append('"id_{attr}"'.format(attr=attribute['attr']))

        if not attribute.get('is_filter'):
            m_agg = re.search(r'(SUM|COUNT|MIN|MAX|AVG)\(.+\)', attribute['expression'].upper())
            if m_agg:
                agg_columns.append(col_title)

            else:
                nagg_columns.append(col_title)

    group_by = None
    if len(agg_columns):
        nagg_columns.insert(0, u'{base_class}_0.id'.format(base_class=view['base_class']))
        group_by = u'GROUP BY %s' % (', '.join(nagg_columns))

    columns.insert(0, u'{base_class}_0.id'.format(base_class=view['base_class']))

    # add id_ columns
    if not group_by:
        for attr_ in dbs.query(SapnsAttribute).\
                join((SapnsClass, SapnsClass.class_id == SapnsAttribute.class_id)).\
                filter(and_(SapnsClass.name == view['base_class'],
                            SapnsAttribute.related_class_id != None,
                            )):

            columns.append(u'{base_class}_0.{attr_name} as "{attr_name}$"'.format(base_class=view['base_class'],
                                                                                  attr_name=attr_.name))

    query  = u'SELECT {columns}\n'.format(columns=',\n'.join(columns))
    query += u'FROM {base_class} {base_class}_0\n'.format(base_class=view['base_class'])
    query += '\n'.join(relations)

    if len(filters):
        # TODO: poder indicar OR
        where_ = u' AND\n'.join(filters)
        query += u'\nWHERE {where}'.format(where=where_)

    if group_by:
        query += u'\n{group_by}'.format(group_by=group_by)

    logger.debug(query)
    return query


def drop_view(view_name):
    logger = logging.getLogger('sapns.lib.sapns.views.drop_view')

    def _exists_view(name):
        e = dbs.execute("SELECT count(*) FROM pg_views WHERE viewname = '{name}'".format(name=name)).fetchone()
        return e[0] == 1

    try:
        # drop "old" view
        if _exists_view(view_name):
            logger.debug(u'Dropping view [{view_name}]'.format(view_name=view_name))
            dbs.execute('DROP VIEW {view_name}'.format(view_name=view_name))
            dbs.flush()
            mark_changed(dbs())

    except Exception, e:
        logger.error(e)


def drop_view_by_id(view_id):
    """
    Drop a view specifying "view_id" (id of "user view" in MongoDB)
    :param view_id:
    """

    # logger = logging.getLogger('sapns.lib.sapns.views.drop_view')

    if isinstance(view_id, (str, unicode)):
        view_id = ObjectId(view_id)

    mdb = Mongo().db

    view = mdb.user_views.find_one(dict(_id=view_id))
    if view is not None:
        mdb.user_views.remove(dict(_id=view_id))


def translate_view(view_):

    logger = logging.getLogger('sapns.lib.sapns.views.translate_view')

    view = deepcopy(view_)

    attributes = []
    mapped_attributes = {}
    for attribute in view['attributes']:
        mapped_attribute = view['attributes_map'][attribute]
        attributes_ = []
        for is_collection, expression in mapped_attribute:

            m_expresion = re.search(r'(\w+)\.(\w+)', expression)
            class_name = m_expresion.group(1)
            attr_name = m_expresion.group(2)

            logger.debug('{class_name}.{attr_name} (is_collection={0})'.format(is_collection,
                                                                               class_name=class_name,
                                                                               attr_name=attr_name))

            attr = SapnsAttribute.by_class_and_name(class_name, attr_name)
            attributes_.append('{0}{1}'.format(COLLECTION_CHAR if is_collection else '', attr.attribute_id))

        a = '#' + '#'.join(attributes_)

        mapped_attributes[attribute] = a
        attributes.append(a)

    view['attributes'] = attributes

    aliases = {}
    for attribute_detail in view['attributes_detail'] + view.get('advanced_filters', []):
        am = mapped_attributes[attribute_detail['path']]
        logger.debug(am)

        attributes_ = []
        for is_collection, attribute_id in re.findall(r'(%s)?(\d+)' % COLLECTION_CHAR, am)[:-1]:
            attributes_.append('{0}{attr_id}'.format(is_collection, attr_id=attribute_id))

        if len(attributes_) == 0:
            attributes_ = ['0']

        old_class_alias = attribute_detail['class_alias']

        class_alias = '{class_name}_{attributes}'.format(class_name=attribute_detail['class_name'],
                                                         attributes='_'.join(attributes_))
        aliases[old_class_alias] = class_alias

        attribute_detail['class_alias'] = class_alias
        attribute_detail['path'] = mapped_attributes[attribute_detail['path']]

    # attributes_detail
    logger.debug('Translating attributes')
    for attribute_detail in view['attributes_detail']:
        for old, new in aliases.iteritems():
            # alumnos -> alumnos.
            old_ = '{0}.'.format(old)
            new_ = '{0}.'.format(new)

            logger.debug('{0} -> {1}'.format(old_, new_))

            attribute_detail['expression'] = attribute_detail['expression'].replace(old_, new_)

    # advanced_filters
    logger.debug('Translating filters')
    for af in view.get('advanced_filters', []):
        for old, new in aliases.iteritems():
            # alumnos -> alumnos.
            old_ = '{0}.'.format(old)
            new_ = '{0}.'.format(new)

            logger.debug('%s -> %s' % (old_, new_))

            af['attr'] = af['attr'].replace(old_, new_)
            af['class_alias'] = af['class_alias'].replace(old_, new_)
            af['expression'] = af['expression'].replace(old_, new_)

    return view


def create_view(view):

    logger = logging.getLogger('sapns.lib.sapns.views.create_view')

    mdb = Mongo().db

    query = get_query(view)

    view_name = get_view_name(view['name'])

    # drop view before is created
    drop_view(view_name)

    # create view
    logger.debug(u'Creating view "{view_name}"'.format(view_name=view_name))
    dbs.execute(u'CREATE VIEW {view_name} AS {query}'.format(view_name=view_name, query=query))
    dbs.flush()

    # create "class" (if it doesn't exist already)
    creation = False
    cls_c = SapnsClass.by_name(view['name'], parent=False)
    if not cls_c:
        logger.debug(u'Creating class "{title}" ({name})'.format(title=view['title'], name=view['name']))
        cls_c = SapnsClass()
        cls_c.name = view['name']
        cls_c.title = view['title']
        cls_c.parent_class_id = SapnsClass.by_name(view['base_class']).class_id

        creation = True

    else:
        # drop old "user view"
        mdb.user_views.remove(dict(_id=ObjectId(cls_c.view_id)))

    view['view_name'] = view_name
    view['creation_date'] = dt.datetime.now()
    view_id = mdb.user_views.insert(view)

    cls_c.view_id = str(view_id)

    dbs.add(cls_c)
    dbs.flush()

    # create "list" permission
    if creation:
        logger.debug(u'Creating "list" permission')
        list_p = SapnsPermission()
        list_p.permission_name = u'{class_name}#list'.format(class_name=cls_c.name)
        list_p.display_name = u'List'
        list_p.class_id = cls_c.class_id
        list_p.type = SapnsPermission.TYPE_LIST
        list_p.requires_id = False
        dbs.add(list_p)
        dbs.flush()

    return view_id

OPERATOR_CONTAIN               = 'co'
OPERATOR_EQUAL                 = 'eq'
OPERATOR_LESS_THAN             = 'lt'
OPERATOR_GREATER_THAN          = 'gt'
OPERATOR_LESS_THAN_OR_EQUAL    = 'let'
OPERATOR_GREATER_THAN_OR_EQUAL = 'get'
OPERATOR_NOT_CONTAIN           = 'nco'
OPERATOR_NOT_EQUAL             = 'neq'

_CONSTANT_DATE_TODAY           = 'today'
_CONSTANT_DATE_START_WEEK      = 'start_week'
_CONSTANT_DATE_END_WEEK        = 'end_week'
_CONSTANT_DATE_START_MONTH     = 'start_month'
_CONSTANT_DATE_END_MONTH       = 'end_month'
_CONSTANT_DATE_START_YEAR      = 'start_year'
_CONSTANT_DATE_END_YEAR        = 'end_year'
_CONSTANT_DAY                  = 'd'
_CONSTANT_WEEK                 = 'w'
_CONSTANT_MONTH                = 'm'
_CONSTANT_YEAR                 = 'y'


def filter_title(filter_):
    operators = {OPERATOR_CONTAIN: _(u'Contains'),
                 OPERATOR_EQUAL: _(u'Equals to'),
                 OPERATOR_LESS_THAN: _(u'Less than'),
                 OPERATOR_GREATER_THAN: _(u'Greater than'),
                 OPERATOR_LESS_THAN_OR_EQUAL: _(u'Less than or equals to'),
                 OPERATOR_GREATER_THAN_OR_EQUAL: _(u'Greater than or equals to'),
                 OPERATOR_NOT_CONTAIN: _(u'Does not contain'),
                 OPERATOR_NOT_EQUAL: _(u'Not equals to'),
                 }

    null_value = ''
    if filter_['null_value']:
        null_value = u' (%s)' % filter_['null_value']

    return u'<%s>%s %s "%s"' % (filter_['field'], null_value, operators[filter_['operator']], filter_['value'])


def filter_sql(path, attribute, operator, value, null_value):

    # logger = logging.getLogger('filter_sql')

    attribute_id = int(re.findall(r'#%s?(\d+)' % COLLECTION_CHAR, path)[-1])
    attr = dbs.query(SapnsAttribute).get(attribute_id)

    value_ = None
    null_value_ = None
    if attr.type == SapnsAttribute.TYPE_DATE:

        # value
        date_ = _strtodate(value)
        if date_ is not None:
            value_ = '%.4d-%.2d-%.2d' % (date_.year, date_.month, date_.day)

        else:
            value_ = process_date_constants(value)

        # null_value
        null_date_ = _strtodate(null_value)
        if null_date_ is not None:
            null_value_ = '%.4d-%.2d-%.2d' % (null_date_.year, null_date_.month, null_date_.day)

        else:
            null_value_ = process_date_constants(null_value)

    # {user_id} - id of the user who is actually logged in
    m = re.search(r'^\s*\{\s*user_id\s*}\s*$', value, re.I)
    if m:
        value = request.identity['user'].user_id

    if operator in [OPERATOR_CONTAIN, OPERATOR_NOT_CONTAIN]:

        def no_accents(text_value):
            result = text_value
            result = re.sub(r'(a|á|à|ä)', u'(a|á|à|ä)', result, re.U)
            result = re.sub(r'(e|é|è|ë)', u'(e|é|è|ë)', result, re.U)
            result = re.sub(r'(i|í|ì|ï)', u'(i|í|ì|ï)', result, re.U)
            result = re.sub(r'(o|ó|ò|ö)', u'(o|ó|ò|ö)', result, re.U)
            result = re.sub(r'(u|ú|ù|ü)', u'(u|ú|ù|ü)', result, re.U)

            return result

        if attr.type in [SapnsAttribute.TYPE_STRING, SapnsAttribute.TYPE_MEMO]:
            if operator == OPERATOR_CONTAIN:
                operator_ = u'SIMILAR TO'

            else:
                operator_ = u'NOT SIMILAR TO'

            sql = u"UPPER(%s) %s UPPER('%%%s%%')" % (attribute, operator_, no_accents(value))

    elif operator in [OPERATOR_EQUAL, OPERATOR_NOT_EQUAL]:

        if operator == OPERATOR_EQUAL:
            operator_ = u'='

        elif operator == OPERATOR_NOT_EQUAL:
            operator_ = u'!='

        # string, memo
        if attr.type in [SapnsAttribute.TYPE_STRING, SapnsAttribute.TYPE_MEMO]:
            if value:
                if not null_value:
                    # foo IS NOT NULL AND UPPER(foo) = UPPER(TRIM('bar'))
                    sql = u"%s IS NOT NULL AND UPPER(%s) %s UPPER(TRIM('%s'))" % (attribute, attribute, operator_, value)

                else:
                    # UPPER(COALESCE(foo, 'bar') = UPPER(TRIM('bar'))
                    sql = u"UPPER(COALESCE(%s, '%s')) %s UPPER(TRIM('%s'))" % (attribute, null_value, operator_, value)

            else:
                sql = u"TRIM(COALESCE(%s, '')) %s ''" % (attribute, operator_)

        # date
        elif attr.type == SapnsAttribute.TYPE_DATE:
            if value:
                if not null_value:
                    # foo IS NOT NULL AND foo != '2001-01-01'
                    sql = u"%s IS NOT NULL AND %s %s '%s'" % (attribute, attribute, operator_, value_)
                else:
                    # COALESCE(foo, '1900-01-01') != '2001-01-01'
                    sql = u"COALESCE(%s, '%s') %s '%s'" % (attribute, null_value_, operator_, value_)

            else:
                if operator == OPERATOR_EQUAL:
                    # foo IS NULL
                    sql = u"%s IS NULL" % attribute

                elif operator == OPERATOR_NOT_EQUAL:
                    # foo IS NOT NULL
                    sql = u"%s IS NOT NULL" % attribute

        # time
        elif attr.type == SapnsAttribute.TYPE_TIME:
            if value:
                if not null_value:
                    # foo IS NOT NULL AND foo = '12:30'
                    sql = u"%s IS NOT NULL AND %s %s '%s'" % (attribute, attribute, operator_, value)
                else:
                    # COALESCE(foo, '00:00') = '12:30'
                    sql = u"COALESCE(%s, '%s') %s '%s'" % (attribute, null_value, operator_, value)

            else:
                if operator == OPERATOR_EQUAL:
                    # foo IS NULL
                    sql = u"%s IS NULL" % attribute

                else:
                    # foo IS NOT NULL
                    sql = u"%s IS NOT NULL" % attribute

        # boolean
        elif attr.type == SapnsAttribute.TYPE_BOOLEAN:

            if value:
                # equals to non-empty = true
                if operator == OPERATOR_EQUAL:
                    sql = attribute

                else:
                    # OPERATOR_NOT_EQUAL
                    # not equal to non-empty = false
                    sql = u'NOT {0}'.format(attribute)

            else:
                # equals to empty = false
                if operator == OPERATOR_EQUAL:
                    sql = u'NOT {0}'.format(attribute)

                else:
                    # OPERATOR_NOT_EQUAL
                    # not equal to empty = true
                    sql = attribute

        # everything else (int, float, ...)
        else:
            if value:
                if not null_value:
                    # foo IS NOT NULL AND foo = 123
                    sql = u"%s IS NOT NULL AND %s %s %s" % (attribute, attribute, operator_, value)
                else:
                    # COALESCE(foo, 0) = 123
                    sql = u"COALESCE(%s, %s) %s %s" % (attribute, null_value, operator_, value)

            else:
                if operator == OPERATOR_EQUAL:
                    # foo IS NULL
                    sql = u"%s IS NULL" % attribute

                else:
                    # foo IS NOT NULL
                    sql = u"%s IS NOT NULL" % attribute

    elif operator in [OPERATOR_LESS_THAN, OPERATOR_GREATER_THAN,
                      OPERATOR_LESS_THAN_OR_EQUAL, OPERATOR_GREATER_THAN_OR_EQUAL]:

        if operator == OPERATOR_LESS_THAN:
            operator_ = u'<'

        elif operator == OPERATOR_GREATER_THAN:
            operator_ = u'>'

        elif operator == OPERATOR_LESS_THAN_OR_EQUAL:
            operator_ = u'<='

        elif operator == OPERATOR_GREATER_THAN_OR_EQUAL:
            operator_ = u'>='

        # date
        if attr.type == SapnsAttribute.TYPE_DATE:
            if not null_value:
                # foo IS NOT NULL AND foo > '2001-01-01'
                sql = u"%s IS NOT NULL AND %s %s '%s'" % (attribute, attribute, operator_, value_)
            else:
                # COALESCE(foo, '1900-01-01') > '2001-01-01'
                sql = u"COALESCE(%s, '%s') %s '%s'" % (attribute, null_value_, operator_, value_)

        # string, memo, time
        elif attr.type in [SapnsAttribute.TYPE_STRING, SapnsAttribute.TYPE_MEMO, SapnsAttribute.TYPE_TIME]:
            if not null_value:
                # foo IS NOT NULL AND foo > 'hola'
                sql = u"%s IS NOT NULL AND %s %s '%s'" % (attribute, attribute, operator_, value)
            else:
                # COALESCE(foo, 'aaa') > 'hola'
                sql = u"COALESCE(%s, '%s') %s '%s'" % (attribute, null_value, operator_, value)

        # everything else (int, float, ...)
        else:
            if not null_value:
                # foo IS NOT NULL AND foo < 123
                sql = u'%s IS NOT NULL AND %s %s %s' % (attribute, attribute, operator_, value)
            else:
                # COALESCE(foo, 0) < 123
                sql = u'COALESCE(%s, %s) %s %s' % (attribute, null_value, operator_, value)

    return sql


def process_date_constants(value):

    # logger = logging.getLogger('process_date_constants')

    def _sub(m):
        cons = m.group(1)
        s = m.group(3)
        q = int(m.group(4) or 0)
        t = m.group(5) or _CONSTANT_DAY

        r = None
        if cons == _CONSTANT_DATE_TODAY:
            r = dt.date.today()

        elif cons == _CONSTANT_DATE_START_WEEK:
            wd = dt.date.today().weekday()
            r = dt.date.today() - dt.timedelta(days=wd)

        elif cons == _CONSTANT_DATE_END_WEEK:
            wd = 6 - dt.date.today().weekday()
            r = dt.date.today() + dt.timedelta(days=wd)

        elif cons == _CONSTANT_DATE_START_MONTH:
            today = dt.date.today()
            r = dt.date(today.year, today.month, 1)

        elif cons == _CONSTANT_DATE_END_MONTH:
            today = dt.date.today()
            next_month = today + dt.timedelta(days=30)
            r = dt.date(next_month.year, next_month.month, 1) - dt.timedelta(days=1)

        elif cons == _CONSTANT_DATE_START_YEAR:
            today = dt.date.today()
            r = dt.date(today.year, 1, 1)

        elif cons == _CONSTANT_DATE_END_YEAR:
            today = dt.date.today()
            r = dt.date(today.year, 12, 31)

        if r:
            if s and q:
                if t == _CONSTANT_DAY:
                    if s == '-':
                        n = -q
                    else:
                        n = q

                    r = r + dt.timedelta(days=n)

                elif t == _CONSTANT_WEEK:
                    if s == '-':
                        n = -q * 7
                    else:
                        n = q * 7

                    r = r + dt.timedelta(days=n)

                elif t == _CONSTANT_MONTH:

                    r_ = r

                    if s == '-':
                        n = -1
                    else:
                        n = +1

                    i = 0
                    while abs(i) != q:
                        next_month = r_ + dt.timedelta(days=30*n)
                        r_ = dt.date(next_month.year, next_month.month, r.day)

                        i += n

                    r = r_

                elif t == _CONSTANT_YEAR:
                    if s == '-':
                        n = -q

                    else:
                        n = +q

                    r = dt.date(r.year + n, r.month, r.day)

            return r.strftime('%Y-%m-%d')

        else:
            return m.group(0)

    return re.sub(r'\{\s*(\w+)(\s+([\+\-])\s*(\d+)\s*(\w?))?\s*}', _sub, value)
