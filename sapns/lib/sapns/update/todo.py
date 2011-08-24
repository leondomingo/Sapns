# -*- coding: utf-8 -*-

TODO = [
    # example SQL
    dict(code='example_sql', desc='example_sql', type='sql', 
         filename='example_sql/example.sql'),
    # example PY
    dict(code='example_py', desc='example_py', type='py', 
         module='example_py.example'),
    # get_roles
    dict(code='init: get_roles', desc='get_roles', type='sql', 
         filename='init/get_roles.function.sql'),
    # has_role
    dict(code='init: has_role', desc='has_role', type='sql', 
         filename='init/has_role.function.sql'),
    # sp_actions
    dict(code='init: sp_permission', desc='sp_permission', type='sql', 
         filename='init/sp_permission.view.sql'),
    # sp_attr_privileges
    dict(code='init: sp_attr_privileges', desc='sp_attr_privileges', type='sql', 
         filename='init/sp_attr_privileges.view.sql'),
    # sp_attributes
    dict(code='init: sp_attributes', desc='sp_attributes', type='sql', 
         filename='init/sp_attributes.view.sql'),
    # sp_classes
    dict(code='init: sp_classes', desc='sp_classes', type='sql', 
         filename='init/sp_classes.view.sql'),
    # sp_docs
    dict(code='init: sp_docs', type='sql', filename='init/sp_docs.view.sql'),
    # sp_users
    dict(code='init: sp_users', desc='sp_users', type='sql', 
         filename='init/sp_users.view.sql'),
    # sp_roles
    dict(code='init: sp_roles', desc='sp_roles', type='sql',
         filename='init/sp_roles.view.sql'),
    # roles/users privileges
    dict(code='init: roles/users privileges', type='py', 
         module='init.privileges'),
]