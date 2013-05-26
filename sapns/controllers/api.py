# -*- coding: utf-8 -*-

from sapns.lib.base import BaseController
from sapns.controllers.components import ComponentsController

class APIController(BaseController):

    components = ComponentsController()
