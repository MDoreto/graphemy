from sqlmodel import Field

from graphemy.dl import Dl
from graphemy.models import Graphemy
from graphemy.router import GraphemyRouter
from graphemy.setup import Setup
import os
def import_files(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                module_name = os.path.splitext(file)[0]
                module_path = os.path.join(root, module_name)
                module_path_rel = os.path.relpath(os.path.join(root, module_name))
                module_path = module_path_rel.replace(os.path.sep, '.')
                exec(f'import {module_path}')