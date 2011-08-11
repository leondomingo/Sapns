# -*- coding: utf-8 -*-

from sapns.model import DBSession as dbs
from pylons.i18n import ugettext as _
# more imports here...

def update():
    print _('Ok')
    print dbs.bind