-- __code__ = sapns: logs view
CREATE OR REPLACE VIEW _view_sp_logs AS 
  SELECT l.id, cast(l.when_ as date) AS "Date", 
    date_trunc('seconds', cast(l.when_ as time)) as "Time",
    u.display_name AS "Who", l.what AS "What", l.description AS "Description", 
    c.title AS "Table", l.row_id AS "Row ID", l.auto AS "Auto"
  FROM sp_logs l
  LEFT JOIN sp_users u ON u.id = l.who
  JOIN sp_classes c on c.name = l.table_name;