-- __code__ = init: has_role
CREATE OR REPLACE FUNCTION has_role(user_id integer, role_name text)
  RETURNS boolean AS
$BODY$
begin
  return (
    select count(*)
    from sp_user_role
    join sp_roles on 
      sp_roles.id = sp_user_role.id_role and
      upper(sp_roles."name") = upper(role_name)
    where sp_user_role.id_user = user_id) > 0;
end;
$BODY$
LANGUAGE plpgsql;