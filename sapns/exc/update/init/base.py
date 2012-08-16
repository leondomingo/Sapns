# -*- coding: utf-8 -*-

from sapns.model.sapnsmodel import SapnsClass, SapnsAttribute, SapnsRole, \
    SapnsPermission
from sqlalchemy.sql.expression import and_, func

_lower = func.lower

class BaseUpdate(object):
    
    def __init__(self): #, dbs):
        self.dbs = None #dbs
        
    def _class_by_name(self, cls_name):
        """
        IN
          cls_name  <unicode>
          
          The following examples are equivalent:
            c = self._class_by_name(u'foo')
            c = self._class_by_name(u'FOO')
            c = self._class_by_name(u'Foo')
          
        OUT
          <SapnsClass>
        """
        
        return self.dbs.query(SapnsClass).\
            filter(_lower(SapnsClass.name) == _lower(cls_name)).\
            first()
    
    def _attr_by_name(self, cls_name, attr_name):
        """
        IN
          cls_name   <unicode>
          attr_name  <unicode>
          
          The following examples are equivalent:
            a = self._attr_by_name(u'foo', u'bar')
            a = self._attr_by_name(u'FOO', u'BAR')
            a = self._attr_by_name(u'Foo', u'Bar')
          
        OUT
          <SapnsAttribute>
        """
        return self.dbs.query(SapnsAttribute).\
            join((SapnsClass,
                  SapnsClass.class_id == SapnsAttribute.class_id)).\
            filter(and_(_lower(SapnsClass.name) == _lower(cls_name),
                        _lower(SapnsAttribute.name) == _lower(attr_name),
                        )).\
            first()
    
    def _rol_by_name(self, role_name):
        """
        IN
          role_name  <unicode>
          
          The following examples are equivalent:
            r = self._role_by_name(u'managers')
            r = self._role_by_name(u'MANAGERS')
            r = self._role_by_name(u'Managers')
          
        OUT
          <SapnsRole>
        """
        return self.dbs.query(SapnsRole).\
            filter(_lower(SapnsRole.group_name) == _lower(role_name)).\
            first()
    
    def _perm_by_name(self, perm_name):
        """
        IN
          perm_name  <unicode>
          
          The following examples are equivalent:
            p = self._perm_by_name(u'foo#bar')
            p = self._perm_by_name(u'FOO#BAR')
            p = self._perm_by_name(u'Foo#Bar')
          
        OUT
          <SapnsPermission>
        """
        return self.dbs.query(SapnsPermission).\
            filter(_lower(SapnsPermission.permission_name) == _lower(perm_name)).\
            first()