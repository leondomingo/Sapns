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
    SapnsAssignedDoc, SapnsClass, SapnsDocType, SapnsDocFormat

import os
import logging
import simplejson as sj #@UnresolvedImport
from neptuno.dataset import DataSet
from neptuno.postgres.search import search
from neptuno.dict import Dict
from neptuno.util import get_paramw
import sqlalchemy as sa
from sqlalchemy.sql.expression import and_

__all__ = ['DocsController']

#REPO_BASE_PATH = config.get('app.repo_base')

class DocsController(BaseController):
    
    allow_only = authorize.not_anonymous()
    
    @expose('sapns/docs/index.html')
    def index(self, cls, id, **kw):
        
        # TODO: comprobar permisos

        class_ = SapnsClass.by_name(cls)
        id_object = int(id)
        
        filters = [('id_class', class_.class_id), ('id_object', id_object)]
        ds = search(dbs, '_view_sp_docs', filters=filters)
        
        cols = []
        for col in ds.labels:
            w = 125
            if col == 'id':
                w = 60
                
            cols.append(dict(title=col, width=w, align='center'))
            
        rp = get_paramw(kw, 'rp', int, opcional=True, por_defecto=10)
        pag_n = get_paramw(kw, 'pag_n', int, opcional=True, por_defecto=1)
        #show_ids = strtobool(show_ids)
        pos = (pag_n-1) * rp
            
        # total number of pages
        total_pag = 1
        if rp > 0:
            total_pag = ds.count/rp
            
            if ds.count % rp != 0:
                total_pag += 1
            
            if total_pag == 0:
                total_pag = 1
        
        # rows in this page
        totalp = ds.count - pos
        if rp and totalp > rp:
            totalp = rp

        return dict(page='object-docs', 
                    obj=dict(id_class=class_.class_id, id=id_object,
                             title=SapnsClass.object_title(cls, id_object)),
                    grid=dict(caption='Docs', name='docs', cls='sp_docs',
                              search_url=url('/dashboard/docs/'), 
                              cols=cols, 
                              data=ds.to_data(), 
                              actions=[], 
                              pag_n=pag_n, rp=rp, pos=pos,
                              totalp=totalp, total=ds.count, total_pag=total_pag
                              ))
    
    @expose('sapns/docs/index.html')
    @require(authorize.has_any_permission('manage', 'docs'))
    def all(self, **kw):
        came_from = kw.get('came_from')
        
        doclist = DataSet(['title', 'format', 'type', 'author', 'repo'])
        
        for i in xrange(30):
            doclist.append(dict(title='Title %d' % i,
                                format='Format %d' % i,
                                type='Type %d' % i,
                                author='Author %d' % i,
                                repo='Repo %d' % i,
                                ))
        
        return dict(page='all-docs', doclist=doclist, came_from=came_from)
    
    @expose('sapns/docs/edit.html')
    @require(authorize.has_any_permission('manage', 'docs'))
    def edit(self, **kw):
        id_doc = get_paramw(kw, 'id_doc', int, opcional=True)
        #id_class = get_paramw(kw, 'id_class', int)
        #id_object = get_paramw(kw, 'id_object', int)
        
        doc = Dict(repo=None)
        
        # lookup repositories
        repos = dbs.query(SapnsRepo).all()
        if len(repos) == 1:
            doc.id_repo = repos[0].repo_id
            
        if id_doc:
            # edit doc
            doc_ = dbs.query(SapnsDoc).get(id_doc)
            doc.id_author = doc_.author_id
        
        else:
            # new doc
            doc_ = SapnsDoc()
            doc.id_author = request.identity['user'].user_id
                        
        doc.title = doc_.title
        doc.id_type = doc_.doctype_id
        doc.id_format = doc_.docformat_id
        doc.filename = doc_.filename
        
        return dict(doc=doc)
    
    @expose('json')
    @require(authorize.has_any_permission('manage', 'docs'))
    def save(self, **kw):

        logger = logging.getLogger('DocsController.save')
        try:
            # collect params
            id_author = request.identity['user'].user_id
            
            id_object = get_paramw(kw, 'id_object', int)
            id_class = get_paramw(kw, 'id_class', int)
            
            title = get_paramw(kw, 'title', unicode)
            id_type = get_paramw(kw, 'id_type', int)
            id_format = get_paramw(kw, 'id_format', int)
            id_repo = get_paramw(kw, 'id_repo', int)
            file_name = get_paramw(kw, 'file_name', unicode)
            
            id_doc = get_paramw(kw, 'id_doc', int, opcional=True)
    
            # create doc
            if id_doc:
                # edit
                new_doc = dbs.query(SapnsDoc).get(id_doc)
                
            else:
                # create
                new_doc = SapnsDoc()
                
            new_doc.repo_id = id_repo
            new_doc.doctype_id = id_type
            new_doc.docformat_id = id_format
            new_doc.author_id = id_author
            new_doc.filename = file_name
            new_doc.title = title
            
            dbs.add(new_doc)
            dbs.flush()
            
            if not id_doc:
                # (only at creation)
                # assign doc to object/class
                assigned_doc = SapnsAssignedDoc()
                assigned_doc.doc_id = new_doc.doc_id
                assigned_doc.class_id = id_class
                assigned_doc.object_id = id_object
                
                dbs.add(assigned_doc)
                dbs.flush()
            
            return dict(status=True)
    
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e).decode('utf-8'))
        
    @expose('json')
    @require(authorize.has_any_permission('manage', 'docs'))
    def delete(self, id_doc):

        logger = logging.getLogger('DocsController.delete')        
        try:
            id_doc = int(id_doc)
            doc = dbs.query(SapnsDoc).get(id_doc)
            
            # TODO: remove file from disk
            self.remove_file(file_name=doc.filename, id_repo=doc.repo_id)
            
            # remove doc
            dbs.query(SapnsDoc).filter(SapnsDoc.doc_id == id_doc).delete()
            
            dbs.flush()
            
            return dict(status=True)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e).decode('utf-8'))

    @expose()
    @require(authorize.has_any_permission('manage', 'docs'))
    def upload_file(self, f, **kw):
        
        logger = logging.getLogger('DocsController.upload_file')
        try:
            import hashlib as hl
            import random
            
            logger.info(kw)

            # create hash
            s256 = hl.sha256()
            
            random.seed()
            s256.update('%s%6.6d' % (f.filename, random.randint(0, 999999)))
            
            file_name = s256.hexdigest()
            
            # repo
            id_repo = get_paramw(kw, 'id_repo', int)
            
            repo = dbs.query(SapnsRepo).get(id_repo)
            if not repo:
                raise Exception(_('Repo [%d] was not found') % id_repo)
            
            f.file.seek(0)
            with file(os.path.join(repo.abs_path(), file_name), 'wb') as fu:
                fu.write(f.file.read())
            
            return sj.dumps(dict(status=True, 
                                 uploaded_file=f.filename,
                                 file_name=file_name))
        
        except Exception, e:
            logger.error(e)
            return sj.dumps(dict(status=False, message=str(e).decode('utf-8')))
        
    @expose('json')
    @require(authorize.has_any_permission('manage', 'docs'))
    def remove_file(self, **kw):
        
        logger = logging.getLogger('DocsController.remove_file')
        try:
            file_name = get_paramw(kw, 'file_name', unicode)
            id_repo = get_paramw(kw, 'id_repo', int)
            
            repo = dbs.query(SapnsRepo).get(id_repo)
            if not repo:
                raise Exception(_('Repo [%d] was not found') % id_repo)
            
            path_file = os.path.join(repo.abs_path(), file_name) 
            if os.access(path_file, os.F_OK):
                os.remove(path_file)
            
            return dict(status=True)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e).decode('utf-8'))