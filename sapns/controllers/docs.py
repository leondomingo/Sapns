# -*- coding: utf-8 -*-

"""Documents controller"""
from neptuno.dict import Dict
from neptuno.postgres.search import search
from neptuno.util import get_paramw
from pylons.i18n import ugettext as _
from repoze.what import authorize, predicates as p
from sapns.lib.base import BaseController
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsDoc, SapnsRepo, SapnsClass
from tg import expose, config, request, require, response
import logging
import simplejson as sj #@UnresolvedImport

__all__ = ['DocsController']

class DocsController(BaseController):
    
    allow_only = authorize.not_anonymous()
    
    @expose('sapns/docs/index.html')
    def default(self, cls, id, **kw):
        
        # TODO: comprobar permisos
        
        class_ = SapnsClass.by_name(cls)
        id_object = int(id)
        
        title = SapnsClass.object_title(cls, id_object)
        
        return dict(page='',
                    came_from=kw.get('came_from'), 
                    obj=dict(id_class=class_.class_id, 
                             id=id_object,
                             title=title),
                    grid=dict(caption=_('Documents of [%s]') % title,
                              cls=cls,
                              id_object=id_object,
                              ))
        
    @expose('json')
    @require(p.Any(p.in_group('managers'), p.has_any_permission('manage', 'docs')))
    def search(self, cls, id, **kw):
        
        class_ = SapnsClass.by_name(cls)
        id_object = int(id)
        
        # picking up parameters
        q = get_paramw(kw, 'q', unicode, opcional=True, por_defecto='')
        rp = get_paramw(kw, 'rp', int, opcional=True, por_defecto=10)
        pag_n = get_paramw(kw, 'pag_n', int, opcional=True, por_defecto=1)
        pos = (pag_n-1) * rp
        
        filters = [('id_class', class_.class_id), ('id_object', id_object)]
        view_name = '%ssp_docs' % config.get('views_prefix', '_view_') 
        ds = search(dbs, view_name, q=q.encode('utf-8'), rp=rp, offset=pos,
                    filters=filters)
        
        cols = []
        for col in ds.labels:
            w = 125
            if col == 'id':
                w = 60
                
            cols.append(dict(title=col, width=w, align='center'))
            
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
            
        # rows in this page
        this_page = ds.count - pos
        if rp and this_page > rp:
            this_page = rp
            
        return dict(status=True, cols=cols, data=ds.to_data(), 
                    this_page=this_page, total_count=ds.count, total_pag=total_pag)
    
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
        doc.id_repo = doc_.repo_id
        
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
                new_doc.register(id_class, id_object)
                
            return dict(status=True)
    
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e).decode('utf-8'))
        
    @expose('json')
    @require(authorize.has_any_permission('manage', 'docs'))
    def delete(self, id_doc):

        logger = logging.getLogger('DocsController.delete')        
        try:
            SapnsDoc.delete_doc(int(id_doc))
            return dict(status=True)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e).decode('utf-8'))

    @expose()
    @require(authorize.has_any_permission('manage', 'docs'))
    def upload_file(self, f, **kw):
        
        logger = logging.getLogger('DocsController.upload_file')
        try:
            id_repo = get_paramw(kw, 'id_repo', int)
            r = SapnsDoc.upload(f, id_repo)
            
            return sj.dumps(dict(status=True, 
                                 uploaded_file=r['uploaded_file'],
                                 file_name=r['file_name'],
                                 file_size=r['file_size'],
                                 ))
        
        except Exception, e:
            logger.error(e)
            return sj.dumps(dict(status=False, message=str(e).decode('utf-8')))
        
    @expose()
    @require(p.Any(p.in_group('managers'), p.has_any_permission('manage', 'docs')))
    def download(self, id_doc):
        
        content, mt, file_name = SapnsDoc.download(int(id_doc))
        response.headerlist.append(('Content-Type', mt.encode('utf-8')))
        response.headerlist.append(('Content-Disposition', 'attachment;filename=%s' % file_name))
        
        return content
        
    @expose('json')
    @require(authorize.has_any_permission('manage', 'docs'))
    def remove_file(self, **kw):
        
        logger = logging.getLogger('DocsController.remove_file')
        try:
            file_name = get_paramw(kw, 'file_name', unicode)
            id_repo = get_paramw(kw, 'id_repo', int)
            
            SapnsDoc.remove_file(id_repo, file_name)
            
            return dict(status=True)
        
        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e).decode('utf-8'))