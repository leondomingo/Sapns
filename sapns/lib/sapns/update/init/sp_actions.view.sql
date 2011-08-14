CREATE OR REPLACE VIEW _view_sp_actions AS 
  SELECT act.id, act.name AS "Name", act.type AS "Type", 
    act.url AS "URL", cls.name AS "Class"
  FROM sp_actions act
  JOIN sp_classes cls ON cls.id = act.id_class;