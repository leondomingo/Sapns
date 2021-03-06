# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs, SapnsPermission, SapnsClass, SapnsRole
import simplejson as sj

class ImportViews(object):
    
    __code__ = u'init. import views'
    
    def __call__(self):
        
        export_v = SapnsPermission()
        export_v.permission_name = u'sp_classes#import_view'
        export_v.display_name = u'Import view'
        export_v.class_id = SapnsClass.by_name(u'sp_classes').class_id
        export_v.url = u'/dashboard/views/import_view/'
        export_v.type = SapnsPermission.TYPE_PROCESS
        export_v.requires_id = True
        export_v.data = sj.dumps(dict(param_name=u'id_class',
                                    button_title=u'Import',
                                    callback=u'import_view',
                                    width=700,
                                    height=150,
                                    refresh=True,
                                    ))
        
        dbs.add(export_v)
        dbs.flush()
        
        managers = SapnsRole.by_name(u'managers')
        managers.permissions_.append(export_v)
        dbs.flush()