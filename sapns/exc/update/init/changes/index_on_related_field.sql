-- __ignore__
-- __desc__   = 2012-03-29 LD
create or replace function search_index(class_name varchar, idx_name varchar) 
  returns boolean as
$$
begin
  return (SELECT count(*)
          FROM pg_class
          WHERE oid IN (
            SELECT indexrelid
            FROM pg_index, pg_class
            WHERE
              pg_class.relname = class_name AND
              pg_class.oid = pg_index.indrelid AND 
              not indisunique AND 
              not indisprimary
         ) and relname = idx_name) > 0;
end;
$$
language plpgsql;