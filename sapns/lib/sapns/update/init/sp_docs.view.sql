create view _view_sp_docs as
select d.id, d.title as "Title", f.name as "Format", t.name as "Type", 
  u.display_name as "Author", r.name as "Repo", a.id_class, a.object_id as id_object
from sp_docs d
join sp_assigned_docs a on d.id = a.id_doc
left join sp_doctypes t on t.id = d.id_doctype
join sp_docformats f on t.id = d.id_docformat
join sp_users u on u.id = d.id_author
join sp_repos r on r.id = d.id_repo