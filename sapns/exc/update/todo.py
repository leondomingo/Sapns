# -*- coding: utf-8 -*-

TODO = [
    # example SQL
    dict(code=u'example_sql', desc='example_sql', type='sql', 
         filename='example_sql/example.sql'),
    # example PY
    dict(code=u'example_py', desc='example_py', type='py', 
         module='example_py.example'),
    # get_roles
    dict(code=u'init: get_roles', desc='get_roles', type='sql', 
         filename='init/get_roles.function.sql'),
    # has_role
    dict(code=u'init: has_role', desc='has_role', type='sql', 
         filename='init/has_role.function.sql'),
    # sp_actions
    dict(code=u'init: sp_permission', desc='sp_permission', type='sql', 
         filename='init/sp_permission.view.sql'),
    # sp_attr_privileges
    dict(code=u'init: sp_attr_privileges', desc='sp_attr_privileges', type='sql', 
         filename='init/sp_attr_privileges.view.sql'),
    # sp_attributes
    dict(code=u'init: sp_attributes', desc='sp_attributes', type='sql', 
         filename='init/sp_attributes.view.sql'),
    # sp_classes
    dict(code=u'init: sp_classes', desc='sp_classes', type='sql', 
         filename='init/sp_classes.view.sql'),
    # sp_docs
    dict(code=u'init: sp_docs', type='sql', filename='init/sp_docs.view.sql'),
    # sp_users
    dict(code=u'init: sp_users', desc='sp_users', type='sql', 
         filename='init/sp_users.view.sql'),
    # sp_roles
    dict(code=u'init: sp_roles', desc='sp_roles', type='sql',
         filename='init/sp_roles.view.sql'),
    # roles/users privileges
    dict(code=u'init: roles/users privileges', type='py', 
         module='init.privileges'),
    # roles: copy privileges
    dict(code=u'init: copy privileges', type='py', 
         module='init.copy_privileges'),
    # users/roles
    dict(code=u'init: users/roles', type='py',
         module='init.users_roles'),
    # test1
    dict(code=u'sapns: test1_sql', type='sql', filename='init/test1.sql'),
    dict(code=u'sapns: test1_py', type='py', module='init.test1'),
    # users edit
    dict(code=u'sapns: users edit', type='py', module='init.users_edit'),
    # logs view
    dict(code=u'sapns: logs view', type='sql', filename='init/logs_view.sql'),
]