-- code: init: sp_docs
CREATE OR REPLACE VIEW _view_sp_docs AS 
 SELECT d.id, d.title AS "Title", f.name AS "Format", t.name AS "Type", 
   u.display_name AS "Author", r.name AS "Repo", 
   a.id_class, a.object_id AS id_object
   FROM sp_docs d
   JOIN sp_assigned_docs a ON d.id = a.id_doc
   LEFT JOIN sp_doctypes t ON t.id = d.id_doctype
   JOIN sp_docformats f ON f.id = d.id_docformat
   JOIN sp_users u ON u.id = d.id_author
   JOIN sp_repos r ON r.id = d.id_repo;