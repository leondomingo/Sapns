# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser
from tg import request

def get_user(cls=None):
    if cls is None:
        cls = SapnsUser
        
    return dbs.query(cls).get(request.identity['user'].user_id)
