# -*- coding: utf-8 -*-
"""Documents controller"""

# turbogears imports
from tg import expose, url, config, redirect, request, require

# third party imports
from pylons import cache
from pylons.i18n import ugettext as _
from pylons.i18n import lazy_ugettext as l_
from repoze.what import authorize, predicates

# project specific imports
from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser , SapnsDoc, SapnsRepo,\
    SapnsAssignedDoc

import logging
import simplejson as sj
from neptuno.dataset import DataSet
from neptuno.util import get_paramw

__all__ = ['DocsController']

class DocsController(BaseController):
    
    allow_only = authorize.not_anonymous()
    
    @expose('sapns/docs/index.html')
    def index(self, **kw):
        came_from = kw.get('came_from')
        
        doclist = DataSet(['title', 'format', 'type', 'author'])
        for i in xrange(30):
            doclist.append(dict(title='Title %d' % ((i+1)*100),
                                format='Format %d' % i,
                                type='Type %d' % i,
                                author='Author %d' % i))

        return dict(page='user-docs', doclist=doclist, came_from=came_from)
    
    @expose('sapns/docs/index.html')
    @require(authorize.has_any_permission('manage', 'docs'))
    def all(self, **kw):
        came_from = kw.get('came_from')
        
        doclist = DataSet(['title', 'format', 'type', 'author'])
        for i in xrange(30):
            doclist.append(dict(title='Title %d' % i,
                                format='Format %d' % i,
                                type='Type %d' % i,
                                author='Author %d' % i))
        
        return dict(page='all-docs', doclist=doclist, came_from=came_from)

    @expose()
    def upload_file(self, fichero, **kw):
        
        logger = logging.getLogger('DocsController.upload_file')
        try:
            import os
            import hashlib as hl
            import random

            # create hash
            s256 = hl.sha256()
            
            random.seed()
            s256.update('%s%6.6d' % (fichero.filename, random.randint(0, 999999)))
            
            file_name = s256.hexdigest()
            
            # TODO: get repo base path
            REPO_BASE_PATH = '/home/leon/workspace/sapns/sapns/public/repo'
            
            # collect params
            id_author = request.identity['user'].user_id
            
            id_object = get_paramw(kw, 'id_object', int)
            id_class = get_paramw(kw, 'id_class', int)
            
            title = get_paramw(kw, 'title', unicode)
            id_type = get_paramw(kw, 'id_type', int)
            id_format = get_paramw(kw, 'id_format', int)
            
            # repo
            id_repo = get_paramw(kw, 'id_repo', int)
            
            repo = dbs.query(SapnsRepo).get(id_repo)
            REPO_PATH = os.path.join(REPO_BASE_PATH, repo.path)
            
            # create doc
            new_doc = SapnsDoc()
            new_doc.repo_id = id_repo
            new_doc.doctype_id = id_type
            new_doc.docformat_id = id_format
            new_doc.author_id = id_author
            new_doc.filename = file_name
            new_doc.title = title
            
            dbs.add(new_doc)
            dbs.flush()
            
            # assign doc
            assigned_doc = SapnsAssignedDoc()
            assigned_doc.doc_id = new_doc.doc_id
            assigned_doc.class_id = id_class
            assigned_doc.object_id = id_object
            
            dbs.add(assigned_doc)
            dbs.flush()
            
            fichero.file.seek(0)
            with file(os.path.join(REPO_PATH, file_name), 'wb') as f:
                f.write(fichero.file.read())
            
            return sj.dumps(dict(status=True, 
                                 id_doc=new_doc.doc_id,
                                 file_name=fichero.filename))
        
        except Exception, e:
            logger.error(e)
            return sj.dumps(dict(status=False, message=unicode(e)))