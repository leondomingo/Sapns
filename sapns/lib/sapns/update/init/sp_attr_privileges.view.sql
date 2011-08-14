CREATE OR REPLACE VIEW _view_sp_attr_privileges AS 
  SELECT attr_p.id, cls.name AS "{{_('Class name')}}", attr.name AS "{{_('Name')}}", 
    attr_p.access AS "{{_('Access')}}", usr.user_name AS "{{_('User')}}", 
    rol.name AS "{{_('Role')}}"
  FROM sp_attr_privileges attr_p
  JOIN sp_attributes attr ON attr.id = attr_p.id_attribute
  JOIN sp_classes cls ON cls.id = attr.id_class
  LEFT JOIN sp_users usr ON usr.id = attr_p.id_user
  LEFT JOIN sp_roles rol ON rol.id = attr_p.id_role;