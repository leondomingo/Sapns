# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs, SapnsDoc


def delete_(*args):
    """
        :param args
        args[0] = cls (unused)
        args[1] = ids
    """

    for doc_id in args[1]:
        doc = dbs.query(SapnsDoc).get(doc_id)

        doc.remove_file(doc.repo_id, doc.filename)

        dbs.query(SapnsDoc).filter(SapnsDoc.doc_id == doc_id).delete()
        dbs.flush()
