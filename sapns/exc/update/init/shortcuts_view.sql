-- __code__ = init. shortcuts view

create or replace view view_sp_shortcuts as
    select s.id, s.title as "Title", u.display_name as "User", p.title as "Parent", 
        s.order as "Order", perm.display_name as "Permission", perm.name as "Permission name"
    from sp_shortcuts s
    left join sp_users u on u.id = s.id_user
    left join sp_shortcuts p on p.id = s.id_parent_shortcut
    left join sp_permission as perm on perm.id = s.id_permission;