# -*- coding: utf-8 -*-
"""Dashboard Controller"""

from neptuno.postgres.search import Search
from neptuno.util import strtobool, strtodate, strtotime, datetostr, get_paramw
from pylons.i18n import ugettext as _
from sapns.controllers.logs import LogsController
from sapns.controllers.messages import MessagesController
from sapns.controllers.privileges import PrivilegesController
from sapns.controllers.roles import RolesController
from sapns.controllers.shortcuts import ShortcutsController
from sapns.controllers.users import UsersController
from sapns.controllers.util import UtilController
from sapns.controllers.views import ViewsController
from sapns.lib.base import BaseController
from sapns.lib.sapns.const_sapns import ROLE_MANAGERS
from sapns.lib.sapns.htmltopdf import url2
from sapns.lib.sapns.lists import EListForbidden
from sapns.lib.sapns.users import get_user
from sapns.lib.sapns.util import add_language, init_lang, get_languages, get_template, topdf, \
    format_float, datetostr as _datetostr, timetostr as _timetostr, get_list, log_access
from sapns.model import DBSession as dbs
from sapns.model.sapnsmodel import SapnsUser, SapnsShortcut, SapnsClass, \
    SapnsAttribute, SapnsAttrPrivilege, SapnsPermission, SapnsLog
from zope.sqlalchemy import mark_changed
from sqlalchemy import Table
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.schema import MetaData
from tg import response, expose, require, url, request, redirect, config, predicates as p
import tg
from cStringIO import StringIO
import datetime as dt
import logging
import re
import simplejson as sj
from sapns.lib.sapns.mongo import Mongo
from bson.objectid import ObjectId
import sapns.lib.sapns.to_xls as toxls
import sapns.lib.sapns.merge as sapns_merge
from webob.exc import HTTPForbidden


class TasksController(BaseController):
    pass
