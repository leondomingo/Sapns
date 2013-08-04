# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsClass
from sqlalchemy.schema import MetaData, Table


def delete_(cls, ids):

    cls_ = SapnsClass.by_name(cls)

    # delete record/s
    meta = MetaData(dbs.bind)
    tbl = Table(cls_.name, meta, autoload=True)
    tbl.delete(tbl.c.id.in_(ids)).execute()
    dbs.flush()
