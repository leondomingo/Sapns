# -*- coding: utf-8 -*-

from bson.objectid import ObjectId
from pylons.i18n import ugettext as _
from sapns.lib.sapns.util import strtodate as _strtodate, datetostr as _datetostr
from sapns.lib.sapns.mongo import Mongo
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsAttribute, SapnsClass, SapnsPermission
from tg import config
import datetime as dt
import logging
import re
from copy import deepcopy
import simplejson as sj

# might be anything except a number (0, 1, 2, ...) or # (sharp symbol)
COLLECTION_CHAR = 'c'

def get_query(view_id):
    
    logger = logging.getLogger('sapns.lib.sapns.views.get_query')
    
    mdb = Mongo().db

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
            alias_ = '%s_0' % alias_
            
        logger.debug((alias_, attribute_.name,))
        return (alias_, attribute_.name,)
    
    columns = []
    filters = []
    relations = []
    relations_ = {}
    nagg_columns = []
    agg_columns = []
    
    _cmp = lambda x,y: cmp(x.get('order', 0), y.get('order', 0))
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
                    relations__.insert(0, u'LEFT JOIN %s %s ON %s.id = %s.%s' % (attribute['class_name'], attribute['class_alias'],
                                                                                 parent_alias,
                                                                                 attribute['class_alias'], parent_attribute))
                
                else:
                    relations__.insert(0, u'LEFT JOIN %s %s ON %s.id = %s.%s' % (attribute['class_name'], attribute['class_alias'],
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
                                                                                             parent_alias, parent_attribute_,
                                                                                             ))
                            
                            else:
                                relations__.insert(0, u'LEFT JOIN %s %s ON %s.id = %s.%s' % (parent_class, parent_alias,
                                                                                             parent_alias,
                                                                                             parent_alias_, parent_attribute_,
                                                                                             ))
                        
                        parent_alias = parent_alias_
                        
                    else:
                        end_ = True
                        
                relations += relations__
        
        if not attribute.get('is_filter'):
            col_title = '"%s"' % attribute['title']    
            columns.append(u'%s as %s' % (attribute['expression'], col_title))
        else:
            filters.append(attribute['expression'])
        
        m_agg = re.search(r'(SUM|COUNT|MIN|MAX|AVG)\([\w\,\.]+\)', attribute['expression'].upper())
        if m_agg:
            agg_columns.append(col_title)
            
        else:
            nagg_columns.append(col_title)
            
    group_by = None
    if not len(agg_columns):
        columns.insert(0, '%s_0.id' % view['base_class'])
        
    else:
        group_by = 'GROUP BY %s' % (', '.join(nagg_columns))
        
    query =  u'SELECT %s\n' % (',\n'.join(columns))
    query += u'FROM %s %s_0\n' % (view['base_class'], view['base_class'])
    query += '\n'.join(relations)

    if len(filters):
        # TODO: poder indicar OR
        where_ = ' AND\n'.join(filters)
        query += '\nWHERE %s' % where_
    
    if group_by:
        query += '\n%s' % group_by
        
    logger.debug(query)
    return query

def drop_view(view_name):
    logger = logging.getLogger('sapns.lib.sapns.views.drop_view')
    
    def _exists_view(name):
        e = dbs.execute("SELECT count(*) FROM pg_views WHERE viewname = '%s' " % name).fetchone()
        return e[0] == 1
    
    try:
        # drop "old" view
        if _exists_view(view_name):
            logger.debug(u'Dropping view [%s]' % view_name)
            dbs.execute('DROP VIEW %s' % view_name)
            dbs.flush()
            
            c = SapnsClass.by_name('sp_classes')
            c.class_id = c.class_id
            dbs.add(c)
            dbs.flush()
        
    except Exception, e:
        logger.error(e)
        
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

            logger.debug('%s.%s (is_collection=%s)' % (class_name, attr_name, is_collection))

            attr = SapnsAttribute.by_class_and_name(class_name, attr_name)
            attributes_.append('%s%s' % (COLLECTION_CHAR if is_collection else '', attr.attribute_id))
    
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
            attributes_.append('%s%s' % (is_collection, attribute_id))
            
        if len(attributes_) == 0:
            attributes_ = ['0']
            
        old_class_alias = attribute_detail['class_alias']
        
        class_alias = '%s_%s' % (attribute_detail['class_name'], '_'.join(attributes_))
        aliases[old_class_alias] = class_alias
    
        attribute_detail['class_alias'] = class_alias
        
        attribute_detail['path'] = mapped_attributes[attribute_detail['path']]
        
    # attributes_detail
    logger.debug('Translating attributes')
    for attribute_detail in view['attributes_detail']:
        for old, new in aliases.iteritems():
            # alumnos -> alumnos.
            old_ = '%s.' % old
            new_ = '%s.' % new
            
            logger.debug('%s -> %s' % (old_, new_))

            attribute_detail['expression'] = attribute_detail['expression'].replace(old_, new_)

    # advanced_filters
    logger.debug('Translating filters')
    for af in view.get('advanced_filters', []):
        for old, new in aliases.iteritems():
            # alumnos -> alumnos.
            old_ = '%s.' % old
            new_ = '%s.' % new
            
            logger.debug('%s -> %s' % (old_, new_))

            af['attr'] = af['attr'].replace(old_, new_)
            af['class_alias'] = af['class_alias'].replace(old_, new_)
            af['expression'] = af['expression'].replace(old_, new_)
            
    return view    

def create_view(view):
    
    logger = logging.getLogger('sapns.lib.sapns.views.create_view')
    
    mdb = Mongo().db

    query = get_query(view)
    
    view_name = '%s%s' % (config.get('views_prefix', '_view_'), view['name'])

    # drop view before is created    
    drop_view(view_name)
    
    # create view
    logger.debug(u'Creating view "%s"' % view_name)
    dbs.execute('CREATE VIEW %s AS %s' % (view_name, query))
    dbs.flush()
    
    # create "class" (if it don't exist already)
    creation = False
    cls_c = SapnsClass.by_name(view['name'], parent=False)
    if not cls_c:
        logger.debug(u'Creating class "%s" (%s)' % (view['title'], view['name']))
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
        list_p.permission_name = u'%s#list' % cls_c.name
        list_p.display_name = u'List'
        list_p.class_id = cls_c.class_id
        list_p.type = SapnsPermission.TYPE_LIST
        list_p.requires_id = False
        dbs.add(list_p)
        dbs.flush()
    
    return view_id

OPERATOR_CONTAIN = 'co'
OPERATOR_EQUAL = 'eq'
OPERATOR_LESS_THAN = 'lt'
OPERATOR_GREATER_THAN = 'gt'
OPERATOR_LESS_THAN_OR_EQUAL = 'let'
OPERATOR_GREATER_THAN_OR_EQUAL = 'get'
OPERATOR_NOT_CONTAIN = 'nco'
OPERATOR_NOT_EQUAL = 'neq'

_CONSTANT_DATE_TODAY       = 'today'
_CONSTANT_DATE_START_WEEK  = 'start_week'
_CONSTANT_DATE_END_WEEK    = 'end_week'
_CONSTANT_DATE_START_MONTH = 'start_month'
_CONSTANT_DATE_END_MONTH   = 'end_month'
_CONSTANT_DATE_START_YEAR  = 'start_year'
_CONSTANT_DATE_END_YEAR    = 'end_year'
_CONSTANT_DAY              = 'd'
_CONSTANT_WEEK             = 'w'
_CONSTANT_MONTH            = 'm'
_CONSTANT_YEAR             = 'y'

def filter_title(filter_):
    operators = { OPERATOR_CONTAIN: _(u'Contains'),
                  OPERATOR_EQUAL: _(u'Equals to'),
                  OPERATOR_LESS_THAN: _(u'Less than'),
                  OPERATOR_GREATER_THAN: _(u'Greater than'),
                  OPERATOR_LESS_THAN_OR_EQUAL: _(u'Less than or equals to'),
                  OPERATOR_GREATER_THAN_OR_EQUAL: _(u'Greater than or equals to'),
                  OPERATOR_NOT_CONTAIN: _(u'Does not contain'),
                  OPERATOR_NOT_EQUAL: _(u'Not equals to'),
                }

    return u'<%s> %s "%s"' % (filter_['field'], operators[filter_['operator']], filter_['value'])

def filter_sql(path, attribute, operator, value):

    logger = logging.getLogger('filter_sql')

    attribute_id = int(re.findall(r'#%s?(\d+)' % COLLECTION_CHAR, path)[-1])
    attr = dbs.query(SapnsAttribute).get(attribute_id)

    value_ = None
    if attr.type == SapnsAttribute.TYPE_DATE:
        date_ = _strtodate(value)
        if date_ is not None:
            value_ = '%.4d-%.2d-%.2d' % (date_.year, date_.month, date_.day)

        else:
            value_ = process_date_constants(value)

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

        if attr.type in [SapnsAttribute.TYPE_STRING, SapnsAttribute.TYPE_MEMO]:
            if value:
                sql = u"%s IS NOT NULL AND UPPER(%s) %s UPPER(TRIM('%s'))" % (attribute, attribute, operator_, value)

            else:
                sql = u"TRIM(COALESCE(%s, '')) %s ''" % (attribute, operator_)

        elif attr.type == SapnsAttribute.TYPE_DATE:
            if value:
                sql = u"%s IS NOT NULL AND %s %s '%s'" % (attribute, attribute, operator_, value_)

            else:
                if operator == OPERATOR_EQUAL:
                    sql = u"%s IS NULL" % attribute

                elif operator == OPERATOR_NOT_EQUAL:
                    sql = u"%s IS NOT NULL" % attribute

        elif attr.type == SapnsAttribute.TYPE_TIME:
            if value:
                sql = u"%s IS NOT NULL AND %s %s '%s'" % (attribute, attribute, operator_, value)

            else:
                if operator == OPERATOR_EQUAL:
                    sql = u"%s IS NULL" % attribute

                else:
                    sql = u"%s IS NOT NULL" % attribute

        else:
            if value:
                sql = u"%s IS NOT NULL AND %s %s %s" % (attribute, attribute, operator_, value)

            else:
                if operator == OPERATOR_EQUAL:
                    sql = u"%s IS NULL" % attribute

                else:
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

        if attr.type in [SapnsAttribute.TYPE_INTEGER, SapnsAttribute.TYPE_FLOAT]:
            sql = u'%s IS NOT NULL AND %s %s %s' % (attribute, attribute, operator_, value)

        elif attr.type == SapnsAttribute.TYPE_DATE:
            sql = u"%s IS NOT NULL AND %s %s '%s'" % (attribute, attribute, operator_, value_)

        elif attr.type in [SapnsAttribute.TYPE_STRING, SapnsAttribute.TYPE_MEMO, SapnsAttribute.TYPE_TIME]:
            sql = u"%s IS NOT NULL AND %s %s '%s'" % (attribute, attribute, operator_, value)

        else:
            sql = u"%s IS NOT NULL AND %s %s %s" % (attribute, attribute, operator_, value)

    return sql

def process_date_constants(value):

    logger = logging.getLogger('process_date_constants')
    
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
                        n = -q*7
                    else:
                        n = q*7
                    
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
    
    return re.sub(r'\{\s*(\w+)(\s+([\+\-])\s*(\d+)\s*(\w{0,1}))?\s*\}', _sub, value)