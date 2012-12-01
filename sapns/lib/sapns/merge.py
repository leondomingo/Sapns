# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsClass, SapnsAttribute
from sqlalchemy.schema import MetaData, Table
import logging
import transaction

class EMerge(Exception):
    pass

def merge(cls, id_to, from_ids):
    """
    IN
      cls        <str>
      id_to      <int>
      from_ids   [<int>, ...]
      
      merge('clientes', 31, [118399, 70110])
    """
    
    _logger = logging.getLogger('merge')

    class_ = SapnsClass.by_name(cls)
    meta = MetaData(bind=dbs.bind)
    t = Table(cls, meta, autoload=True)
    
    transaction.begin()
    try:
        for id_another in from_ids:
            
            another = dbs.execute(t.select(t.c.id == id_another)).fetchone()
            if not another:
                raise EMerge('Record %s of "%s" does not exist' % (id_another, cls))
            
            for r_atr in dbs.query(SapnsAttribute).\
                    filter(SapnsAttribute.related_class_id == class_.class_id):
                
                # update
                _logger.info('Updating "%s.%s"' % (r_atr.class_.name, r_atr.name))
                t_ = Table(r_atr.class_.name, meta, autoload=True)
                values = {}
                values[r_atr.name.encode('utf-8')] = id_to
                
                update_ = t_.update(t_.c[r_atr.name.encode('utf-8')] == id_another, values=values)
                dbs.execute(update_)
                dbs.flush()
                
            # remove
            _logger.info('Removing %d from "%s"' % (id_another, cls))
            delete_ = t.delete(t.c.id == id_another)
            dbs.execute(delete_)
            dbs.flush()
            
        class_.name = class_.name
        dbs.add(class_)
        dbs.flush()
            
        transaction.commit()
        
    except Exception, e:
        _logger.error(e)
        transaction.abort()
        raise