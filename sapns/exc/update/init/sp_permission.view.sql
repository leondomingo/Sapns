-- code: init: sp_permission
CREATE OR REPLACE VIEW _view_sp_permission AS 
  SELECT perm.id, perm.name AS "Name", perm.type AS "Type", 
    perm.url AS "URL", cls.name AS "Class"
  FROM sp_permission perm
  JOIN sp_classes cls ON cls.id = perm.id_class;