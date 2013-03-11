# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs
from sapns.lib.sapns.mongo import Mongo
from bson.objectid import ObjectId
import re
from sapns.model.sapnsmodel import SapnsAttribute
import logging

COLLECTION_CHAR = 'c'

def get_query(view_id):
    
    _logger = logging.getLogger('sapns.lib.sapns.views.get_query')
    
    mdb = Mongo().db
    
    if isinstance(view_id, (str, unicode,)):
        view_id = ObjectId(view_id)
    
    view = mdb.user_views.find_one(dict(_id=view_id))
    
    def _get_parent(alias):
        
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
            
        return (alias_, attribute_.name,)
    
    columns = []
    relations = []
    relations_ = {}
    nagg_columns = []
    agg_columns = []
    for attribute in sorted(view['attributes_detail'], cmp=lambda x,y: cmp(x.get('order', 0), y.get('order', 0))):
        
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
        
        col_title = '"%s"' % attribute['title']    
        columns.append(u'%s as %s' % (attribute['expression'], col_title))
        
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
    
    if group_by:
        query += '\n%s' % group_by
        
    #_logger.info(query)
    return query