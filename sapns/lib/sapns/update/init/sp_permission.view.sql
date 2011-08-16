CREATE OR REPLACE VIEW _view_sp_permission AS 
  SELECT perm.id, perm.name AS "Name", act.type AS "Type", 
    perm.url AS "URL", cls.name AS "Class"
  FROM sp_permission perm
  JOIN sp_classes cls ON cls.id = act.id_class;