# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsClass, SapnsAttribute
from sqlalchemy.schema import MetaData, Table
import logging
import transaction
from zope.sqlalchemy import mark_changed


class EMerge(Exception):
    pass


def merge(cls, id_to, from_ids, not_included=None):
    """
    IN
      cls          <str>
      id_to        <int>
      from_ids     [<int>, ...]
      not_included [<str>, ...] (optional)

      merge('clientes', 31, [118399, 70110])
    """

    logger = logging.getLogger('merge')

    class_ = SapnsClass.by_name(cls)
    meta = MetaData(bind=dbs.bind)
    t = Table(cls, meta, autoload=True)

    transaction.begin()
    try:
        for id_another in from_ids:

            another = dbs.execute(t.select(t.c.id == id_another)).fetchone()
            if not another:
                raise EMerge(u'Record %s of "%s" does not exist' % (id_another, cls))

            for r_atr in dbs.query(SapnsAttribute).\
                    filter(SapnsAttribute.related_class_id == class_.class_id):

                # update
                logger.info(u'Updating "%s.%s"' % (r_atr.class_.name, r_atr.name))
                r_cls = r_atr.class_.name
                if not_included and r_cls in not_included:
                    continue

                t_ = Table(r_cls, meta, autoload=True)
                values = {r_atr.name.encode('utf-8'): id_to}
                update_ = t_.update(t_.c[r_atr.name.encode('utf-8')] == id_another, values=values)

                dbs.execute(update_)
                dbs.flush()

            # remove
            logger.info(u'Removing %d from "%s"' % (id_another, cls))
            delete_ = t.delete(t.c.id == id_another)
            dbs.execute(delete_)
            dbs.flush()

        mark_changed(dbs())

        transaction.commit()

    except Exception, e:
        logger.error(e)
        transaction.abort()
        raise
