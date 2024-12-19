import importlib
from pathlib import Path

from sqlmodel import Field

from graphemy.dl import Dl
from graphemy.models import Graphemy
from graphemy.router import GraphemyRouter
from graphemy.setup import Setup

__all__ = ["Dl", "Field", "Graphemy", "GraphemyRouter", "Setup"]


def import_files(path:Path) -> None:
    """Recursively imports all Python files found in the specified directory and its subdirectories,
    excluding `__init__.py`. This function is intended to facilitate the dynamic loading of modules,
    particularly useful in scenarios like automatic model discovery in web applications.

    Args:
        path (str): The directory path from which Python files should be imported.

    Note:
        - This function modifies the global namespace by dynamically importing modules.
        - Import paths are adjusted to be relative, considering the package structure.

    """
    for py_file in Path(path).rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        # Convert the file path to a module path by removing the .py suffix,
        # making it relative to `path`, and joining with dots.
        module_path = ".".join(py_file.with_suffix("").relative_to(path).parts)
        importlib.import_module(module_path)
