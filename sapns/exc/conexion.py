# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker

class Conexion(object):
    
    def __init__(self, sa_url):
        
        self.engine = create_engine(sa_url.decode('utf-8'), pool_size=1, pool_recycle=30)
        
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
    def __del__(self):        
        self.session.close()        
        self.engine.dispose()