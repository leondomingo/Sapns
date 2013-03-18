# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs, SapnsPermission, SapnsClass, SapnsRole
import simplejson as sj

class CopyViews(object):
    
    __code__ = u'init. copy views'
    
    def __call__(self):
        
        copy_v = SapnsPermission()
        copy_v.permission_name = u'sp_classes#copy_view'
        copy_v.display_name = u'Copy view'
        copy_v.class_id = SapnsClass.by_name(u'sp_classes').class_id
        copy_v.url = u'/dashboard/views/copy/'
        copy_v.type = SapnsPermission.TYPE_PROCESS
        copy_v.requires_id = True
        #{"param_name": "id_grupo", "button_title": "Hoja de asistencia", 
        #"callback": "hoja_de_asistencia", "width": 700, "refresh": false, "height": 200}
        copy_v.data = sj.dumps(dict(param_name=u'id_class',
                                    button_title=u'Copy',
                                    callback=u'copy_view',
                                    width=700,
                                    height=200,
                                    refresh=True,
                                    ))
        
        dbs.add(copy_v)
        dbs.flush()
        
        managers = SapnsRole.by_name(u'managers')
        managers.permissions_.append(copy_v)
        dbs.flush()