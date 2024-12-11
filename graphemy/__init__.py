import os

from sqlmodel import Field

from graphemy.dl import Dl
from graphemy.models import Graphemy
from graphemy.router import GraphemyRouter
from graphemy.setup import Setup

__all__ = ["Dl", "Field", "Graphemy", "GraphemyRouter", "Setup"]


def import_files(path) -> None:
    """Recursively imports all Python files found in the specified directory and its subdirectories,
    excluding `__init__.py`. This function is intended to facilitate the dynamic loading of modules,
    particularly useful in scenarios like automatic model discovery in web applications.

    Args:
        path (str): The directory path from which Python files should be imported.

    Note:
        - This function modifies the global namespace by dynamically importing modules.
        - Import paths are adjusted to be relative, considering the package structure.

    """
    for root, _dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                module_name = os.path.splitext(file)[0]
                module_path = os.path.join(root, module_name)
                module_path_rel = os.path.relpath(
                    os.path.join(root, module_name),
                )
                module_path = module_path_rel.replace(os.path.sep, ".")
                exec(f"import {module_path}")
