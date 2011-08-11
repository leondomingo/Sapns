CREATE OR REPLACE VIEW _view_sp_users AS 
  SELECT usr.id, usr.display_name AS "{{_('Display name')}}", 
    usr.user_name AS "{{_('User name')}}", usr.email_address AS "{{_('E-mail')}}", 
    get_roles(usr.id) AS "{{_('Roles')}}"
  FROM sp_users usr;