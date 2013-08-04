# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsPermission
from sqlalchemy.sql.expression import and_
import simplejson as sj
import logging


class DeletePermissions(object):

    __code__ = u'sapns: new delete permission'

    def __call__(self):

        logger = logging.getLogger('DeletePermissions')

        for p in dbs.query(SapnsPermission).\
                filter(and_(SapnsPermission.type == SapnsPermission.TYPE_DELETE)).\
                order_by(SapnsPermission.permission_name):

            logger.info(p.permission_name)

            p.data = sj.dumps(dict(param_name='id_',
                                   button_title=u'Delete',
                                   extra_params=dict(cls=p.class_.name),
                                   width=800,
                                   height=300,
                                   callback='delete_sp',
                                   ))

            dbs.add(p)
            dbs.flush()
