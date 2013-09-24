# -*- coding: utf-8 -*-

"""Documents controller"""
from cStringIO import StringIO
from neptuno.dict import Dict
from neptuno.postgres.search import search
from neptuno.util import get_paramw, datetostr
from pylons.i18n import ugettext as _
from sapns.lib.base import BaseController
from sapns.lib.sapns.const_sapns import ROLE_MANAGERS
from sapns.lib.sapns.util import init_lang, log_access
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsDoc, SapnsRepo, SapnsClass
from tg import expose, config, request, require, response, predicates as p
from zipfile import ZipFile, ZIP_DEFLATED
from sqlalchemy.sql.expression import and_
import datetime as dt
import logging
import simplejson as sj

__all__ = ['DocsController']

class DocsController(BaseController):

    #allow_only = p.not_anonymous()

    @expose('sapns/docs/index.html')
    @require(p.not_anonymous())
    @log_access('documents')
    def _default(self, cls, id_, **kw):

        # TODO: comprobar permisos

        class_ = SapnsClass.by_name(cls)
        id_ = int(id_)

        title = SapnsClass.object_title(cls, id_)

        return dict(page='', came_from=kw.get('came_from'),
                    lang=init_lang(),
                    obj=dict(id_class=class_.class_id,
                             id=id_,
                             title=title),
                    grid=dict(caption=_('Documents of [%s]') % title,
                              cls=cls,
                              id_object=id_,
                              ))

    @expose('json')
    @require(p.Any(p.in_group(ROLE_MANAGERS), p.has_any_permission('manage', 'docs')))
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
    @require(p.Any(p.in_group(ROLE_MANAGERS), p.has_any_permission('manage', 'docs')))
    @log_access('edit document')
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
    @require(p.Any(p.in_group(ROLE_MANAGERS), p.has_any_permission('manage', 'docs')))
    @log_access('save document')
    def save(self, **kw):

        logger = logging.getLogger('DocsController.save')
        try:
            # collect params
            id_author = request.identity['user'].user_id

            id_object = get_paramw(kw, 'id_object', int)
            id_class = get_paramw(kw, 'id_class', int)

            title = get_paramw(kw, 'title', unicode)
            id_type = get_paramw(kw, 'id_type', int, opcional=True)
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
    @require(p.Any(p.in_group(ROLE_MANAGERS), p.has_any_permission('manage', 'docs')))
    @log_access('delete document')
    def delete(self, id_doc):

        logger = logging.getLogger('DocsController.delete')
        try:
            try:
                id_doc = int(id_doc)
                SapnsDoc.delete_doc(id_doc)

            except ValueError:
                docs = sj.loads(id_doc)
                for id_doc in docs:
                    SapnsDoc.delete_doc(id_doc)

            return dict(status=True)

        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e).decode('utf-8'))

    @expose()
    @require(p.Any(p.in_group(ROLE_MANAGERS), p.has_any_permission('manage', 'docs')))
    @log_access('upload file')
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
    @require(p.Any(p.in_group(ROLE_MANAGERS), p.has_any_permission('manage', 'docs')))
    @log_access('download file')
    def download(self, id_doc):
        """
        IN
          id_doc  <int>/<list> [<int>, ...]
        """

        try:
            id_doc = int(id_doc)

            content, mt, file_name = SapnsDoc.download(id_doc)
            response.content_type = mt.encode('latin-1')
            response.headers['Content-Disposition'] = 'attachment;filename=%s' % file_name

            return content

        except ValueError:

            docs = sj.loads(id_doc)

            if len(docs) == 1:
                content, mt, file_name = SapnsDoc.download(docs[0])
                response.content_type = mt.encode('latin-1')
                response.headers['Content-Disposition'] =  'attachment;filename=%s' % file_name

                return content

            else:
                # varios archivos
                zf = StringIO()
                zip_file = ZipFile(zf, 'w', ZIP_DEFLATED)
                try:
                    for id_doc in docs:

                        content, mt, file_name = SapnsDoc.download(int(id_doc))

                        f = StringIO()
                        f.write(content)

                        zip_file.writestr(file_name, f.getvalue())

                finally:
                    zip_file.close()

                response.content_type = 'application/zip'
                fn = _('docs__%s.zip') % datetostr(dt.date.today(), fmt='%Y%m%d')
                response.headers['Content-Disposition'] = 'attachment;filename=%s' % fn

                return zf.getvalue()

    @expose('json')
    @require(p.Any(p.in_group(ROLE_MANAGERS), p.has_any_permission('manage', 'docs')))
    @log_access('remove file')
    def remove_file(self, **kw):
        """
        IN
          file_name <str>
          id_repo   <int>

        OUT
          { status: <bool> }
        """

        logger = logging.getLogger('DocsController.remove_file')
        try:
            file_name = get_paramw(kw, 'file_name', unicode)
            id_repo = get_paramw(kw, 'id_repo', int)

            SapnsDoc.remove_file(id_repo, file_name)

            return dict(status=True)

        except Exception, e:
            logger.error(e)
            return dict(status=False, message=str(e).decode('utf-8'))

    @expose()
    @require(p.not_anonymous())
    def get(self, repo, doc):
        """
        IN
          repo str/int
          doc str/int

          Different ways of calling:
              # by doc id (repo is unnecessary)
              /docs/get/_/1234

              # by repo id and doc filename
              /docs/get/1/asdkasduo12mk2jklj32d3d3kjlk3

              # by repo id and doc title (notice the starting _)
              /docs/get/1/_company_icon

              # by repo name and doc filename
              /docs/get/main repo/asdkasduo12mk2jklj32d3d3kjlk3

              # by repo name and doc title (notice the starting _)
              /docs/get/main repo/_company_icon
        """

        id_doc = SapnsDoc.get_id_doc(repo, doc)

        content, mt, _file_name = SapnsDoc.download(id_doc)
        response.content_type = mt.encode('latin-1')

        return content

    # open to everyone!
    @expose()
    def get_(self, id_repo, filename):

        doc = dbs.query(SapnsDoc).\
            filter(and_(SapnsDoc.repo_id == int(id_repo),
                        SapnsDoc.filename == filename)).\
            first()

        content = ''
        response.content_type = 'text/plain'
        if doc:
            content, mt, _file_name = SapnsDoc.download(doc.doc_id)
            response.content_type = mt.encode('latin-1')

        return content
