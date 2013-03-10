# -*- coding: utf-8 -*-

from decorator import decorator
from pylons.i18n import lazy_ugettext as l_
from pylons.templating import pylons_globals
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsClass, SapnsPermission, SapnsAttribute, \
    SapnsUser, SapnsShortcut, SapnsAttrPrivilege, SapnsRole, SapnsUserRole
from sqlalchemy import MetaData
from sqlalchemy.dialects.postgresql.base import TIME, TIMESTAMP, BYTEA
from sqlalchemy.sql.expression import and_
from sqlalchemy.types import INTEGER, NUMERIC, BIGINT, DATE, TEXT, VARCHAR, \
    BOOLEAN, BLOB
from tg import config, response, request
from tg.i18n import set_lang, get_lang
import logging
import neptuno.util as nutil
import os
import re
import subprocess as sp
import tempfile

ROLE_MANAGERS = u'managers'

def extract_model(all_=False): 
    logger = logging.getLogger('lib.sapns.extract_model')
    
    meta = MetaData(bind=dbs.bind, reflect=True)
    logger.info('Connected to "%s"' % meta.bind)
    
    def sp_cmp(x, y):
        """Alphabetical order but sp_* tables before any other table."""
        
        if x.name.startswith('sp_'):
            if y.name.startswith('sp_'):
                return cmp(x.name, y.name)
            
            else:
                return -1
            
        else:
            if y.name.startswith('sp_'):
                return 1
            
            else:
                return cmp(x.name, y.name)
    
    tables = []
    for tbl in sorted(meta.sorted_tables, cmp=sp_cmp):
        
        if not tbl.name.startswith('sp_') or all_:
            
            logger.info('Table: %s' % tbl.name)
            
            t = dict(name=tbl.name,
                     columns=[])
            
            # class name
            class_name = [i.title() for i in tbl.name.split('_')]
            t['class_name'] = ''.join(class_name)
            
            t['pk'] = [k for k in tbl.primary_key.columns.keys()]
            
            fk_cols = []
            fk_tables = []
            for fk in tbl.foreign_keys:
                logger.info(fk.parent)
                fk_tables.append(fk.column.table)
                fk_cols.append(fk.parent.name)
                
            for c in tbl.columns:
                col = dict(name=c.name, type=repr(c.type), fk='-', 
                           length=None, prec=None, scale=None,
                           pk=False)

                # is primary key?                    
                col['pk'] = c.name in tbl.primary_key.columns.keys()
                
                logger.info('%s' % type(c.type))
                
                type_name = '---'
                if isinstance(c.type, INTEGER):
                    type_name = SapnsAttribute.TYPE_INTEGER
                    
                elif isinstance(c.type, NUMERIC):
                    type_name = SapnsAttribute.TYPE_FLOAT
                    col['prec'] = c.type.precision
                    col['scale'] = c.type.scale
                    
                elif isinstance(c.type, BIGINT):
                    type_name = SapnsAttribute.TYPE_INTEGER

                elif isinstance(c.type, DATE):
                    type_name = SapnsAttribute.TYPE_DATE
                    
                elif isinstance(c.type, TIME):
                    type_name = SapnsAttribute.TYPE_TIME
                    
                elif isinstance(c.type, TIMESTAMP):
                    type_name = SapnsAttribute.TYPE_DATETIME

                elif isinstance(c.type, VARCHAR):
                    type_name = SapnsAttribute.TYPE_STRING
                    col['length'] = c.type.length
                    
                elif isinstance(c.type, TEXT):
                    type_name = SapnsAttribute.TYPE_MEMO
                    
                elif isinstance(c.type, BOOLEAN):
                    type_name = SapnsAttribute.TYPE_BOOLEAN
                    
                elif isinstance(c.type, BLOB):
                    type_name = 'blob'
                    
                elif isinstance(c.type, BYTEA):
                    type_name = 'bytea'
                    
                else:
                    type_name = '(%s)' % str(c.type)
                    
                col['type_name'] = type_name
                
                try:
                    i = fk_cols.index(c.name)
                    col['fk_table'] = fk_tables[i]
                    
                except:
                    col['fk_table'] = None
                    
                t['columns'].append(col)
                
            tables.append(t)
            
    return tables
        
def update_metadata():
    
    logger = logging.getLogger('lib.sapns.update_metadata')
    
    managers = SapnsRole.by_name(ROLE_MANAGERS)
    #managers = SapnsRole()
    
    tables = extract_model(all_=True)
    tables_id = {}
    pending_attr = {}
    for tbl in tables:
        
        logger.info('Table: %s' % tbl['name'])
        
        klass = dbs.query(SapnsClass).\
                    filter(SapnsClass.name == tbl['name']).\
                    first()
        
        if not klass:
            logger.warning('.....creating')
            
            klass = SapnsClass()
            klass.name = tbl['name']
            klass.title = tbl['name'].title()
            desc = unicode(l_('Class: %s'))
            klass.description =  desc % tbl['name']
            
            dbs.add(klass)
            dbs.flush()
            
            # # grant access (r/w) to managers
            managers.add_privilege(klass.class_id)

        else:
            logger.warning('.....already exists')
            
        tables_id[tbl['name']] = klass.class_id
            
        # create an action
        def create_action(name, type_):
            action = dbs.query(SapnsPermission).\
                        filter(and_(SapnsPermission.class_id == klass.class_id,
                                    SapnsPermission.type == type_)).\
                        first()
                            
            if not action:
                action = SapnsPermission()
                action.permission_name = '%s#%s' % (klass.name, name.lower())
                action.display_name = name
                action.type = type_
                action.class_id = klass.class_id
                
                dbs.add(action)
                dbs.flush()
                
                # add this action to "managers" role
                managers.permissions_.append(action)
                dbs.flush()
                
            elif action.type == SapnsPermission.TYPE_LIST:
                for s in action.shortcuts:
                    s.title = action.class_.title
                    dbs.add(s)
                    dbs.flush()
                
        # create standard actions
        create_action(unicode(l_('New')), SapnsPermission.TYPE_NEW)
        create_action(unicode(l_('Edit')), SapnsPermission.TYPE_EDIT)
        create_action(unicode(l_('Delete')), SapnsPermission.TYPE_DELETE)
        create_action(unicode(l_('List')), SapnsPermission.TYPE_LIST)
        create_action(unicode(l_('Docs')), SapnsPermission.TYPE_DOCS)
            
        first_ref = False
        for i, col in enumerate(tbl['columns']):
            
            logger.info('Column: %s' % col['name'])
            
            attr = dbs.query(SapnsAttribute).\
                    filter(and_(SapnsAttribute.name == col['name'],
                                SapnsAttribute.class_id == klass.class_id, 
                                )).\
                    first()
                    
            if not attr and col['name'] != 'id':
                logger.warning('.....creating')
                
                attr = SapnsAttribute()
                attr.name = col['name']
                attr.title = col['name'].replace('_', ' ').title()
                attr.class_id = klass.class_id
                attr.type = col['type_name']
                if attr.type == SapnsAttribute.TYPE_STRING and not first_ref:
                    attr.reference_order = 0
                    first_ref = True
                    
                attr.visible = True
                attr.insertion_order = i
                
                if attr.type == SapnsAttribute.TYPE_INTEGER and \
                not attr.name.startswith('id_'):
                    # signed
                    attr.field_regex = r'^\s*(\+|\-)?\d+\s*$'
                    
                elif attr.type == SapnsAttribute.TYPE_FLOAT:
                    # signed
                    # col['prec']
                    # col['scale']
                    attr.field_regex = r'^\s*(\+|\-)?\d{1,%d}(\.\d{1,%d})?\s*$' % \
                        (col['prec']-col['scale'],
                         col['scale'])
                        
                elif attr.type == SapnsAttribute.TYPE_TIME:
                    attr.field_regex = r'^\s*([01][0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?\s*$'
                
                dbs.add(attr)
                dbs.flush()
                
                # grant access (r/w) to managers
                rw_access = SapnsAttrPrivilege.ACCESS_READWRITE
                managers.add_attr_privilege(attr.attribute_id, rw_access)
                
            else:
                logger.warning('.....already exists')
                
                # fill the "field_regex"
                if attr and not attr.field_regex:
                    if attr.type == SapnsAttribute.TYPE_INTEGER and \
                    not attr.name.startswith('id_'):
                        # signed
                        attr.field_regex = r'^\s*(\+|\-)?\d+\s*$'
                        
                    elif attr.type == SapnsAttribute.TYPE_FLOAT:
                        # signed
                        attr.field_regex = r'^\s*(\+|\-)?\d{1,%d}(\.\d{1,%d})?\s*$' % \
                            (col['prec'] - col['scale'], col['scale'])
                            
                    elif attr.type == SapnsAttribute.TYPE_TIME:
                        attr.field_regex = r'^\s*([01][0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?\s*$'
                
            # foreign key
            if col['fk_table'] != None:
                pending_attr[attr.attribute_id] = col['fk_table'].name
        
    # update related classes
    for attr_id, fk_table in pending_attr.iteritems():
        attr = dbs.query(SapnsAttribute).get(attr_id)
        attr.related_class_id = tables_id[fk_table]
        
        dbs.add(attr)
        dbs.flush()
    
    
def create_dashboards(us):
    
    logger = logging.getLogger('lib.sapns.util.create_dashboards')
    
    #us = dbs.query(SapnsUser).get(id_user)
        
    logger.info('Creating dashboard for "%s"' % us.display_name)
    
    # user's dashboard
    dboard = us.get_dashboard()
    if not dboard:
        
        dboard = SapnsShortcut()
        dboard.user_id = us.user_id
        dboard.parent_id = None
        dboard.title = unicode(l_('Dashboard'))
        dboard.order = 0
        
        dbs.add(dboard)
        dbs.flush()
        
        # data exploration
        
        data_ex = SapnsShortcut()
        data_ex.title = unicode(l_('Data exploration'))
        data_ex.parent_id = dboard.shortcut_id
        data_ex.user_id = us.user_id
        data_ex.order = 0
        
        dbs.add(data_ex)
        dbs.flush()
        
        # Data exploration/Sapns
        sc_sapns = SapnsShortcut()
        sc_sapns.title = 'Sapns'
        sc_sapns.parent_id = data_ex.shortcut_id
        sc_sapns.user_id = us.user_id
        sc_sapns.order = 0
        
        dbs.add(sc_sapns)
        
        # Data exploration/Project
        sc_project = SapnsShortcut()
        sc_project.title = config.get('app.name', unicode(l_('Project')))
        sc_project.parent_id = data_ex.shortcut_id
        sc_project.user_id = us.user_id
        sc_project.order = 1
        
        dbs.add(sc_project)
        dbs.flush()
        
    else:
        logger.info('Dashboard already exists')
        
def create_data_exploration():
    
    managers = SapnsRole.by_name(ROLE_MANAGERS)
    #managers = SapnsRole()
    
    logger = logging.getLogger('lib.sapns.util.create_data_exploration')
    
    tables = extract_model(all_=True) #['tables']

    for us in dbs.query(SapnsUser).\
        join((SapnsUserRole,
              and_(SapnsUserRole.user_id == SapnsUser.user_id,
                   SapnsUserRole.role_id == managers.group_id,
                   ))):
        
        create_dashboards(us)
        
        data_ex = us.get_dataexploration()
        sc_sapns = data_ex.by_order(0)
        sc_project = data_ex.by_order(1)
        
        # data exploration/project       
        for i, tbl in enumerate(tables):
            
            cls = dbs.query(SapnsClass).\
                    filter(SapnsClass.name == tbl['name']).\
                    first()
            
            # look for this table "list" action
            act_table = dbs.query(SapnsPermission).\
                filter(and_(SapnsPermission.type == SapnsPermission.TYPE_LIST,
                            SapnsPermission.class_id == cls.class_id)).\
                first()
                            
            if not act_table:
                act_table = SapnsPermission()
                act_table.permission_name = '%s#%s' % (cls.name, SapnsPermission.TYPE_LIST)
                act_table.display_name = unicode(l_('List'))
                act_table.type = SapnsPermission.TYPE_LIST
                act_table.class_id = cls.class_id
                
                dbs.add(act_table)
                dbs.flush()
                
                # add to "managers" role
                managers.permissions_.append(act_table)
                dbs.flush()
                
            # project
            sc_parent = sc_project.shortcut_id
            if cls.name.startswith('sp_'):
                # sapns
                sc_parent = sc_sapns.shortcut_id
                
            sc_table = dbs.query(SapnsShortcut).\
                    filter(and_(SapnsShortcut.parent_id == sc_parent,
                                SapnsShortcut.permission_id == act_table.permission_id,
                                SapnsShortcut.user_id == us.user_id,
                                )).\
                    first()
                    
            # does this user have this class shortcut?
            if not sc_table:
                sc_table = SapnsShortcut()
                sc_table.title = tbl['name']
                sc_table.parent_id = sc_parent
                sc_table.user_id = us.user_id
                sc_table.permission_id = act_table.permission_id
                sc_table.order = i
    
                dbs.add(sc_table)
                dbs.flush()
            
            else:
                logger.info('Shortcut for "%s" already exists' % cls.title)
                
        # TODO: sort (alphabetically) shortcuts inside "data exploration"
        logger.info('Sorting shortcuts inside "data exploration"')
        i = 0
        for sc in dbs.query(SapnsShortcut).\
                filter(SapnsShortcut.parent_id == sc_project.shortcut_id).\
                order_by(SapnsShortcut.title):
            
            sc.order = i
            dbs.add(sc)
            dbs.flush()
            
            i += 1

def topdf(html_content, check_call=True, **kw):
    
    VERSION_0_9 = '0.9'
    VERSION_0_11 = '0.11'
    
    topdf_path = config.get('htmltopdf.path')
    version = config.get('htmltopdf.version', VERSION_0_9)
    
    fd_html, html_path = tempfile.mkstemp(suffix='.html', prefix='sapns_')
    os.close(fd_html)
    try:
        # save HTML content
        f_input = open(html_path, 'wb')
        try:
            f_input.write(html_content)
        
        finally:
            f_input.close()
            
        if not kw.get('orientation'):
            kw['orientation'] = 'Portrait'
            
        if not kw.get('page_size'):
            kw['page_size'] = 'A3'
        
        if not kw.get('q'):
            kw['q'] = None
            
        if version == VERSION_0_9:
            if not kw.get('disable_pdf_compression'):
                kw['disable-pdf-compression'] = None
                
        elif version == VERSION_0_11:
            if not kw.get('no_pdf_compression'):
                kw['no-pdf-compression'] = None
        
        pdf_content = ''
        fd_pdf, pdf_path = tempfile.mkstemp(suffix='.pdf', prefix='sapns_')
        os.close(fd_pdf)
        
        call_ = sp.check_call
        if not check_call:
            call_ = sp.call
            
        extra_params = []
        for k, v in kw.iteritems():
            
            # page_size               --> page-size
            # disable_pdf_compression --> disable-pdf-compression
            k_ = k.replace('_', '-')
            
            if len(k_) > 1:
                extra_params.append('--%s' % k_)
                
            else:
                extra_params.append('-%s' % k_)

            if v is not None:
                extra_params.append(str(v))
                
        try:
            call_([topdf_path] + extra_params + [html_path, pdf_path])
            
            # get PDF content
            f_output = open(pdf_path, 'rb')
            try:
                pdf_content = f_output.read()
            
            finally:
                f_output.close()
            
        finally:
            if os.access(pdf_path, os.F_OK):
                os.remove(pdf_path)
        
    finally:
        if os.access(html_path, os.F_OK):
            os.remove(html_path)
    
    return pdf_content

def pagination(rp, pag_n, total):
        
    # total number of pages
    pos = (pag_n-1)*(rp or 0)
    total_pag = 1
    if rp > 0:
        total_pag = total/rp
        
        if total % rp != 0:
            total_pag += 1
        
        if total_pag == 0:
            total_pag = 1
    
    # rows in this page
    this_page = total - pos
    if rp and this_page > rp:
        this_page = rp
        
    return (this_page, total_pag,)

def extract_lang(lang_list, pattern):
    if lang_list:
        for item in lang_list:
            if re.match(pattern, item):
                return item
        
    return None

def save_language(lang):
    _language = config.get('app.language_cookie', 'sp_language')
    response.set_cookie(_language, value=lang, max_age=60*60*24*30*365) # 1 year

def init_lang():
    default_lang = extract_lang(get_lang(), r'^[a-z]{2}$')
    _language = config.get('app.language_cookie', 'sp_language') 
    lang = request.cookies.get(_language)
    if not lang:
        lang = default_lang
        save_language(lang)
        
    set_lang(lang)
    
    return lang

def get_languages():
    languages = []
    _languages = config.get('app.languages')
    if _languages:
        for l in _languages.decode('utf-8').split(','):
            l = l.strip()
            m = re.search(r'^(\w+)\#(\w+)$', l, re.U)
            if m:
                languages.append(dict(code=m.group(1),
                                      name=m.group(2)))
                
    return languages

def _add_language(f, *args, **kw):
    
    result = f(*args, **kw)
    
    if not result.get('lang'):
        result[f.lang_key] = init_lang()
        
    if not result.get('languages'):
        result[f.languages_key] = get_languages()
        
    return result

# decorator for add "lang" and "languages" to the resulting dict
def add_language(f): #, lang='lang', languages='languages'):
    f.lang_key = 'lang'
    f.languages_key = 'languages'
    return decorator(_add_language, f)

def get_template(tmpl_name, default_tmpl=None):
    globs = {}
    globs.update(pylons_globals())
    try:
        return globs['app_globals'].jinja2_env.get_template(tmpl_name)
    
    except:
        if default_tmpl:
            return globs['app_globals'].jinja2_env.get_template(default_tmpl)
        else:
            raise

# date/time functions (from and to string)
def strtodate(s):
    date_fmt = config.get('formats.date')
    return nutil.strtodate(s, fmt=date_fmt)

def datetostr(d):
    date_fmt = config.get('formats.date')
    return nutil.datetostr(d, fmt=date_fmt)

def strtotime(s):
    return nutil.strtotime(s)
    
def timetostr(t):
    time_fmt = config.get('formats.time')
    return nutil.timetostr(t, fmt=time_fmt)