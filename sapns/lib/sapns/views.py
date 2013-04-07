# -*- coding: utf-8 -*-

from bson.objectid import ObjectId
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
    attributes_list = sorted(view['attributes_detail'], cmp=_cmp) + view['advanced_filters']
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
            logger.info(u'Dropping view [%s]' % view_name)
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
    logger.debug('starting')
    
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
    for attribute_detail in view['attributes_detail']:
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
        
    for attribute_detail in view['attributes_detail']:
        for old, new in aliases.iteritems():
            # alumnos -> alumnos.
            old_ = '%s.' % old
            new_ = '%s.' % new
            attribute_detail['expression'] = attribute_detail['expression'].replace(old_, new_)
            
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
    cls_c = SapnsClass.by_name(view['name'])
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
    
    view['creation_date'] = dt.datetime.now()
    view_id = mdb.user_views.insert(view)
    
    cls_c.view_id = str(view_id)
    
    dbs.add(cls_c)
    dbs.flush()
    
    # create "list" permission
    if creation:
        logger.info(u'Creating "list" permission')
        list_p = SapnsPermission()
        list_p.permission_name = u'%s#list' % cls_c.name
        list_p.display_name = u'List'
        list_p.class_id = cls_c.class_id
        list_p.type = SapnsPermission.TYPE_LIST
        list_p.requires_id = False
        dbs.add(list_p)
        dbs.flush()
    
    return view_id