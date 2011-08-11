CREATE OR REPLACE VIEW _view_sp_actions AS 
  SELECT act.id, act.name AS "{{_('Name')}}", act.type AS "{{_('Type')}}", 
    act.url AS "URL", cls.name AS "{{_('Class')}}"
  FROM sp_actions act
  JOIN sp_classes cls ON cls.id = act.id_class;