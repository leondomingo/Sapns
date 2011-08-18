#!/usr/bin/env python
# -*- coding: utf-8 -*-

import simplejson as sj #@UnresolvedImport
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from neptuno.conexion import Conexion

DeclarativeBase = declarative_base()

class SapnsClass(DeclarativeBase):
    
    __tablename__ = 'sp_classes'
    
    class_id = sa.Column('id', sa.Integer, primary_key=True)
    name = sa.Column(sa.Unicode(50))
    title = sa.Column(sa.Unicode(100))
    
class SapnsAttribute(DeclarativeBase):
    
    __tablename = 'sp_attributes'
    
    attribute_id = sa.Column('id', sa.Integer, primary_key=True)
    name = sa.Column(sa.Unicode(50))
    title = sa.Column(sa.Unicode(100))
    reference_order = sa.Column(sa.Integer)
    insertion_order = sa.Column(sa.Integer)

if __name__ == '__main__':
    pass