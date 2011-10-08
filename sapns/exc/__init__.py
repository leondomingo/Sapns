# -*- coding: utf-8 -*-

import sys
import os
from jinja2 import Environment, PackageLoader

_pl = PackageLoader('sapns', 'templates')
env = Environment(loader=_pl)