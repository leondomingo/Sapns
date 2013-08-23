# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs, SapnsClass
from sapns.lib.sapns.views import drop_view_by_id, drop_view, get_view_name


def delete_(*args):
    """
        :param args
        args[0] = cls (unused)
        args[1] = ids
    """

    for class_id in args[1]:
        klass = dbs.query(SapnsClass).get(class_id)

        if klass.view_id:
            drop_view_by_id(klass.view_id)

        drop_view(get_view_name(klass.name))

        dbs.query(SapnsClass).filter(SapnsClass.class_id == class_id).delete()
        dbs.flush()
