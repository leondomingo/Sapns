# -*- coding: utf-8 -*-

import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
# directorio superior a este
sys.path.append(os.path.split(current_path)[0])
from config import CONFIG
sys.path = sys.path + CONFIG['paths']

if __name__ == '__main__':
    # TODO: Aquí las operaciones de actualización
    pass