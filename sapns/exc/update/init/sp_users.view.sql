-- code: init: sp_users
CREATE OR REPLACE VIEW _view_sp_users AS 
  SELECT usr.id, usr.display_name AS "Display name", 
    usr.user_name AS "User name", usr.email_address AS "E-mail", 
    get_roles(usr.id) AS "Roles"
  FROM sp_users usr;