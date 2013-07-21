# -*- coding: utf-8 -*-

import logging
from pylons.i18n import ugettext as _
from sapns.model.sapnsmodel import SapnsPermission
# from sapns.controllers.dashboard import ECondition


class Conditions(object):

    def _index_of(self, attributes, attr_name):
        i = 0
        while attributes[i]['name'] != attr_name:
            i += 1

        if attributes[i]['name'] == attr_name:
            return i
        else:
            return -1

    def _find_attr(self, attributes, attr_name):
        i = self._index_of(attributes, attr_name)
        if i != -1:
            return attributes[i]

        else:
            return None

    def sp_permission_before(self, id_, attributes):

        logger = logging.getLogger('sp_permission_before')
        logger.info(attributes)

        def _before_edit(id_, attributes):

            # just an example
#            type_ = self._find_attr(attributes, 'type')
#            if type_:
#                type_['value'] = u'(%d) %s' % (id_, type_['value'])

            return

        def _before_insert(attributes):

            name = self._find_attr(attributes, 'name')
            if name:
                name['value'] = _('(new permission)')

            type_ = self._find_attr(attributes, 'type')
            if type_:
                type_['value'] = SapnsPermission.TYPE_PROCESS
                # just an example
                #type_['read_only'] = True

            return

        if not id_:
            _before_insert(attributes)

        else:
            _before_edit(id_, attributes)

    def sp_permission_save(self, moment, update):
        logger = logging.getLogger('sp_permission_save')
        logger.info(moment)
        logger.info(update)

        # just an example
#        if moment == 'before':
#            name = update.get('name')
#            if name:
#                if len(name) > 2:
#                    raise ECondition('"name" no puede ser mayor de 2')
#
#        if moment == 'after':
#            raise ECondition('Esto es una prueba')

        return
