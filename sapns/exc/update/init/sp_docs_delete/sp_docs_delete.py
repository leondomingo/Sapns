# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs, SapnsPermission
import simplejson as sj


class SapnsDocsDelete(object):

    __code__ = u'sp_docs#delete (new deleter)'

    def __call__(self):

        p = SapnsPermission.by_name('sp_docs#delete')
        data = sj.loads(p.data)

        data['extra_params']['deleter'] = u'sapns.lib.sapns.custom_delete.sp_docs.delete_'

        p.data = sj.dumps(data)
        dbs.add(p)
        dbs.flush()
