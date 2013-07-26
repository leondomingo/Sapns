-- __code__ = sapns: Function "remove_temp_views"

create or replace function remove_temp_views() returns boolean as
$$
declare
    vn text;
begin
    for vn in
      select viewname from pg_views
      where viewname ~ '^_temp_'
    loop
      execute 'drop view ' || vn;
    end loop;

    return TRUE;
end;
$$
language plpgsql;
