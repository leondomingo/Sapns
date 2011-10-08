CREATE OR REPLACE FUNCTION get_roles(user_id integer)
  RETURNS text AS
$BODY$
declare
  r text;
  role_name text;
begin
  r = '';
  for role_name in
    select sp_roles."name" from sp_roles
    join sp_user_role on 
      sp_user_role.id_user = user_id and
      sp_user_role.id_role = sp_roles.id
  loop
    if (r = '') then
      r = role_name;
    else
      r = r || ', ' || role_name;
    end if;
  end loop;

  return r;
end;
$BODY$
LANGUAGE plpgsql;