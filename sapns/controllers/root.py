# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, request, redirect, config
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tg.i18n import set_lang, get_lang
#from tgext.admin.tgadminconfig import TGAdminConfig
#from tgext.admin.controller import AdminController
from repoze.what import predicates

from sapns.lib.base import BaseController
from sapns.model import DBSession
import sapns.config.app_cfg as app_cfg

from neptuno.postgres.search import search

from sapns.controllers.error import ErrorController
from sapns.controllers.views import ViewsController
from tg.controllers.util import urlencode
from sapns.controllers.util import UtilController
from sapns.model.sapnsmodel import SapnsUser, SapnsShortcut, SapnsClass,\
    SapnsPrivilege, SapnsAttribute, SapnsAttrPrivilege

import logging
import re
from sqlalchemy import Table
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.schema import MetaData
from sqlalchemy.sql.expression import and_
import simplejson as sj
from sapns.controllers.users import UsersController
from neptuno.util import strtobool, strtodate, strtotime, datetostr
from sapns.controllers.shortcuts import ShortcutsController

__all__ = ['RootController']


class RootController(BaseController):
    """
    The root controller for the sapns application.

    All the other controllers and WSGI applications should be mounted on this
    controller. For example::

        panel = ControlPanelController()
        another_app = AnotherWSGIApplication()

    Keep in mind that WSGI applications shouldn't be mounted directly: They
    must be wrapped around with :class:`tg.controllers.WSGIAppController`.

    """
    error = ErrorController()
    
    views = ViewsController()
    
    util = UtilController()
    
    users = UsersController()
    
    sc = ShortcutsController()

    @expose('index.html')
    @require(predicates.not_anonymous())
    def index(self, sc_type='list', sc_parent=None):
        curr_lang = get_lang()

        # connected user
        user = DBSession.query(SapnsUser).get(request.identity['user'].user_id)

        # get children shortcuts (shortcuts.parent_id = sc_parent) of the this user
        shortcuts = user.get_shortcuts(id_parent=sc_parent)
        
        if sc_parent:
            sc_parent = DBSession.query(SapnsShortcut).get(sc_parent).parent_id
            
        else:
            sc_parent = None
        
        return dict(page='index', curr_lang=curr_lang, shortcuts=shortcuts, 
                    sc_type=sc_type, sc_parent=sc_parent)
        
    @expose()
    def init(self):
        redirect(url('/util/init'))
        
    @expose('message.html')
    @require(predicates.not_anonymous())
    def message(self, message='Error!', came_from='/'):
        return dict(message=message, came_from=url(came_from))

    @expose('environ.html')
    @require(predicates.has_permission('manage'))
    def environ(self):
        """This method showcases TG's access to the wsgi environment."""
        return dict(environment=request.environ)

#    @expose('authentication.html')
#    def auth(self):
#        """Display some information about auth* on this application."""
#        return dict(page='auth')

    @expose('login.html')
    def login(self, came_from=url('/')):
        """Start the user login."""
        login_counter = request.environ['repoze.who.logins']
        if login_counter > 0:
            flash(_('Wrong credentials'), 'warning')
        return dict(page='login', login_counter=str(login_counter),
                    came_from=came_from)

    @expose()
    def post_login(self, came_from='/'):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.

        """
        if not request.identity:
            login_counter = request.environ['repoze.who.logins'] + 1
            redirect('/login', came_from=came_from, __logins=login_counter)
        userid = request.identity['repoze.who.userid']
        flash(_('Welcome back, %s!') % userid)
        redirect(came_from)

    @expose()
    def post_logout(self, came_from=url('/')):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.

        """
        flash(_('We hope to see you soon!'))
        redirect(came_from)

    @expose('listof.html')
    @require(predicates.not_anonymous())
    def list(self, **params):

        # picking up parameters
        cls = params.get('cls', '')
        q = params.get('q', '')
        rp = params.get('rp', 10)
        pag_n = params.get('pag_n', 1)
        caption = params.get('caption', '')
        show_ids = params.get('show_ids', 'false')
        came_from = params.get('came_from', '/')
        
        # does this user have permission on this table?
        user = DBSession.query(SapnsUser).get(request.identity['user'].user_id)
        
        if not user.has_privilege(cls):
            redirect(url('/message',
                         dict(message=_('Sorry, you do not have privilege on this class'),
                              came_from=came_from)))
        
        rp = int(rp)
        pag_n = int(pag_n)
        show_ids = strtobool(show_ids)
        
        pos = (pag_n-1) * rp

        meta = MetaData(bind=DBSession.bind)
        
        try:
            # TODO: cambiar "vista_busqueda_" por "_view_"
            Table('vista_busqueda_%s' % cls, meta, autoload=True)
            view = 'vista_busqueda_%s' % cls
            
        except NoSuchTableError:
            view = cls
            
        ds = search(DBSession, view, q=q.encode('utf-8'), rp=rp, offset=pos, 
                    show_ids=show_ids)
        
        # Reading global settings
        ds.date_fmt = config.get('grid.date_format', default='%m/%d/%Y')
        ds.time_fmt = config.get('grid.time_format', default='%H:%M')
        ds.true_const = config.get('grid.true_const', default='Yes')
        ds.false_const = config.get('grid.false_const', default='No')
        
        ds.float_fmt = app_cfg.format_float
        
        data = ds.to_data()
        
        cols = []
        for col in ds.labels:
            w = 120
            if col == 'id':
                w = 60
                
            cols.append(dict(title=col,
                             width=w,
                             align='center'))
        
        # actions for this class
        class_ = DBSession.query(SapnsClass).\
                    filter(SapnsClass.name == cls).\
                    first()
                    
        actions = class_.sorted_actions()
        
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
            
        return dict(page='list',
                    q=q,
                    show_ids=show_ids,
                    came_from=url(came_from),
                    link='/list?' + urlencode(dict(cls=cls, q=q, rp=rp, pag_n=pag_n,
                                                   caption=caption, show_ids=show_ids)),
                    grid=dict(caption=caption, name=cls,
                              cls=cls,
                              search_url=url('/list'), 
                              cols=cols, data=data, 
                              actions=actions, pag_n=pag_n, rp=rp, pos=pos,
                              totalp=totalp, total=ds.count, total_pag=total_pag))
        
    @expose()
    def setlang(self, lang='en', came_from='/'):
        set_lang(lang)
        redirect(came_from)
        
    @expose()
    @require(predicates.not_anonymous())
    def save(self, cls='', id='', **params):
        
        logger = logging.getLogger(__name__ + '/save')
        logger.info(params)

        cls = SapnsClass.by_name(cls) #params['cls'])
        came_from = params.get('came_from', '/list?cls=%s' % cls.name)
        
        # does this user have permission on this table?
        user = DBSession.query(SapnsUser).get(request.identity['user'].user_id)
        
        if not user.has_privilege(cls.name):
            redirect(url('/message',
                         dict(message=_('Sorry, you do not have privilege on this class'),
                              came_from=came_from)))

        update = {}
        
        if id != '':
            update['id'] = int(id)
        
        for field_name, field_value in params.iteritems():
            m_field = re.search(r'^fld_(.+)', field_name)
            if m_field:
                field_name_ = m_field.group(1) 
                attr = cls.attr_by_name(field_name_)
                
                # null values
                if field_value == 'null':
                    field_value = None
                    
                else:
                    # integer
                    if attr.type == SapnsAttribute.TYPE_INTEGER:
                        if field_value == '':
                            field_value = None
                        else:
                            field_value = int(field_value)
                    
                    # numeric
                    elif attr.type == SapnsAttribute.TYPE_NUMERIC:
                        if field_value == '':
                            field_value = None
                        else:
                            field_value = float(field_value)
                    
                    # boolean
                    elif attr.type == SapnsAttribute.TYPE_BOOLEAN:
                        field_value = strtobool(field_value)
                        
                    # date
                    elif attr.type == SapnsAttribute.TYPE_DATE:
                        if field_value == '':
                            field_value = None
                        else:
                            field_value = strtodate(field_value)
                    
                    # time
                    elif attr.type == SapnsAttribute.TYPE_TIME:
                        if field_value == '':
                            field_value = None
                        else:
                            field_value = strtotime(field_value)
                    
                    # string types        
                    else:
                        field_value = field_value.strip()
                
                update[field_name_] = field_value
                
        logger.info(update)
                
        meta = MetaData(bind=DBSession.bind)
        tbl = Table(cls.name, meta, autoload=True)
        
        if update.get('id'): #, None):
            logger.info('Updating object [%d] of "%s"' % (update['id'], cls.name))
            tbl.update(whereclause=tbl.c.id == update['id'], values=update).execute()
            
        else:
            logger.info('Inserting new object in "%s"' % cls.name)
            tbl.insert(values=update).execute()
            
        DBSession.flush()
        
        redirect(url(came_from))
        
    @expose('edit.html')
    @require(predicates.not_anonymous())
    def new(self, **params):
        
        cls = params.get('cls')
        #id = params.get('id')
        came_from = params.get('came_from', '/')
        
        redirect(url('/edit'), dict(cls=cls, id='', came_from=came_from))
    
    @expose('edit.html')
    @require(predicates.not_anonymous())
    def edit(self, cls='', id=None, came_from='/'):
        
        logger = logging.getLogger(__name__ + '/edit')
        
        user = request.identity['user']
        
        # does this user have privilege on this class?
        priv_class = DBSession.query(SapnsPrivilege, SapnsClass).\
                join((SapnsClass, 
                      SapnsClass.class_id == SapnsPrivilege.class_id)).\
                filter(and_(SapnsPrivilege.user_id == user.user_id, 
                            SapnsClass.name == cls)).\
                first()
                
        if not priv_class:
            redirect(url('/message',
                         dict(message=_('Sorry, you do not have privilege on this class'),
                              came_from=came_from)))
            
        __, class_ = priv_class
        
        meta = MetaData(DBSession.bind)
        try:
            tbl = Table(cls, meta, autoload=True)
            
        except NoSuchTableError:
            redirect(url('/message', 
                         dict(message=_('This class does not exist'),
                              came_from=came_from)))
            
        date_fmt = config.get('grid.date_format', default='%m/%d/%Y')
        
        # js options
        js_options = dict(date_format=config.get('js.date_format', default='mm-dd-yy'),
                          day_names_min=config.get('js.day_names_min'),
                          month_names=config.get('js.month_names'),
                          first_day=config.get('js.first_day'),
                          )
        
        ref = None
        row = None
        if id:
            row = DBSession.execute(tbl.select(tbl.c.id == id)).fetchone()
            if not row:
                # row does not exist
                redirect(url('/message', 
                             dict(message=_('Record does not exist'),
                                  came_from=came_from)))
                
            # reference
            ref = SapnsClass.object_title(class_.name, id)
            
        # get attributes
        attributes = []
        for attr in DBSession.query(SapnsAttribute).\
                join((SapnsClass, SapnsClass.class_id == SapnsAttribute.class_id)).\
                join((SapnsAttrPrivilege, 
                      and_(SapnsAttrPrivilege.user_id == user.user_id,
                           SapnsAttrPrivilege.attribute_id == SapnsAttribute.attribute_id))).\
                filter(and_(SapnsClass.name == cls,
                            SapnsAttribute.visible == True)).\
                order_by(SapnsAttribute.insertion_order).\
                all():
            
            value = ''
            if row:
                if row[attr.name]:
                    # date
                    if attr.type == SapnsAttribute.TYPE_DATE:
                        value = datetostr(row[attr.name], fmt=date_fmt)
                    
                    # rest of types
                    else:
                        value = row[attr.name] or ''
            
            attributes.append(dict(name=attr.name, title=attr.title, 
                                   type=attr.type, value=value, required=attr.required, 
                                   vals=None))
            
            if attr.related_class_id:
                # vals
                attributes[-1]['vals'] = []
                try:
                    rel_class = DBSession.query(SapnsClass).get(attr.related_class_id)
                    
                    # related_class
                    attributes[-1]['related_class'] = rel_class.name
                    
                    logger.info(rel_class.name)
                    
                    attributes[-1]['vals'] = SapnsClass.class_titles(rel_class.name)
                
                except Exception, e:
                    logger.error(e)
                    attributes[-1]['vals'] = None
                
            
        return dict(cls=cls, title=class_.title, id=id, 
                    related_classes=class_.related_classes(), 
                    attributes=attributes, reference=ref, 
                    js_options=js_options, came_from=url(came_from))
    
    @expose('delete.html')
    def delete(self, cls='', id=None, q=False, came_from='/'):
        
        # does the record exist?
        meta = MetaData(DBSession.bind)
        tbl = Table(cls, meta, autoload=True)
        
        this_record = DBSession.execute(tbl.select(tbl.c.id == id)).fetchone()
        if not this_record:
            # record does not exist
            redirect(url('/message', 
                         dict(message=_('Record does not exist'),
                              came_from=came_from)))
        
        if not q:
            # redirect to the question page
            return dict(cls=cls, id=id, came_from=url(came_from))
            
        # delete record
        tbl.delete(tbl.c.id == id).execute()
        
        redirect(url('/message',
                     dict(message=_('Record was successfully deleted'),
                          came_from=url(came_from))))
        
        redirect(url(came_from))
        
    @expose('order/insert.html')
    @require(predicates.has_permission('manage'))
    def ins_order(self, cls='', came_from='/'):
        
        user = DBSession.query(SapnsUser).get(request.identity['user'].user_id)
        
        # check privilege on this class
        if not user.has_privilege(cls):
            redirect(url('/message', 
                         dict(message=_('Sorry, you do not have privilege on this class'),
                              came_from=came_from)))
            
        class_ = SapnsClass.by_name(cls)
        
        return dict(page='insertion order', insertion=class_.insertion(),
                    title=class_.title, came_from=url(came_from))
        
    @expose()
    def ins_order_save(self, attributes='', title='', came_from='/'):
        
        # save insertion order
        attributes = sj.loads(attributes)
        
        title_saved = False
        
        for attr in attributes:
            
            attribute = DBSession.query(SapnsAttribute).get(attr['id'])
            attribute.title = attr['title']
            attribute.insertion_order = attr['order']
            attribute.required = attr['required']
            attribute.visible = attr['visible']
            
            DBSession.add(attribute)
            
            if not title_saved:
                title_saved = True
                attribute.class_.title = title
                DBSession.add(attribute.class_)
            
            DBSession.flush()
        
        redirect(url(came_from))
    
    @expose('order/reference.html')
    @require(predicates.has_permission('manage'))
    def ref_order(self, cls='', came_from='/'):
        
        user = DBSession.query(SapnsUser).get(request.identity['user'].user_id)
        
        # check privilege on this class
        if not user.has_privilege(cls):
            redirect(url('/message', 
                         dict(message=_('Sorry, you do not have privilege on this class'),
                              came_from=came_from)))
            
        class_ = SapnsClass.by_name(cls)
        
        return dict(page='reference order', reference=class_.reference(all=True), 
                    came_from=url(came_from))
    
    @expose()
    def ref_order_save(self, attributes='', came_from='/'):
        
        # save reference order
        attributes = sj.loads(attributes)
        
        for attr in attributes:
            attribute = DBSession.query(SapnsAttribute).get(attr['id'])
            
            attribute.reference_order = attr['order']
            DBSession.add(attribute)
            DBSession.flush()
        
        redirect(url(came_from))