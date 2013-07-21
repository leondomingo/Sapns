# -*- coding: utf-8 -*-

from sapns.lib.sapns.const_sapns import ROLE_MANAGERS
from sapns.model import DBSession as dbs, SapnsPermission, SapnsRole
from sapns.model.sapnsmodel import SapnsClass


class SpClassesEditView(object):

    __code__ = u'init. sp_classes_edit_view'

    def __call__(self):

        edit_view = SapnsPermission()
        edit_view.class_id = SapnsClass.by_name(u'sp_classes').class_id
        edit_view.display_name = u'Edit view'
        edit_view.permission_name = u'sp_classes#edit_view'
        edit_view.type = SapnsPermission.TYPE_PROCESS
        edit_view.url = u'/dashboard/views/edit/'
        edit_view.requires_id = True

        dbs.add(edit_view)
        dbs.flush()

        create_view = SapnsPermission()
        create_view.class_id = SapnsClass.by_name(u'sp_classes').class_id
        create_view.display_name = u'Create view'
        create_view.permission_name = u'sp_classes#create_view'
        create_view.type = SapnsPermission.TYPE_PROCESS
        create_view.url = u'/dashboard/views/create/'
        create_view.requires_id = False

        dbs.add(create_view)
        dbs.flush()

        managers = SapnsRole.by_name(ROLE_MANAGERS)
        managers.permissions_.append(edit_view)
        managers.permissions_.append(create_view)
        dbs.flush()
