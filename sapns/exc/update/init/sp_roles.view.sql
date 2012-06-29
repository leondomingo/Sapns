-- code: init: sp_roles
create view _view_sp_roles
as
select rol.id, rol.name as "Name"
from sp_roles rol;