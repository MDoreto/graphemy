import importlib
import sys
from pathlib import Path

from sqlmodel import Field

from graphemy.dl import Dl
from graphemy.models import Graphemy
from graphemy.router import GraphemyRouter
from graphemy.setup import Setup

# Expose these names when doing `from graphemy import *`
__all__ = ["Dl", "Field", "Graphemy", "GraphemyRouter", "Setup"]


def import_files(path: Path) -> None:
    """
    Recursively import all Python files under a given directory, except __init__.py.

    This function dynamically loads Python modules to ensure that any side effects
    (e.g., model registration, schema generation) occur upon importing them. It
    can be particularly useful in frameworks where models or routes must be
    discovered automatically.

    Args:
        path (Path): The directory (or subdirectory) to search for Python files
            to import.
    """
    root_dir = path.resolve()
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))
    for py_file in path.rglob("*.py"):
        # Skip __init__.py to avoid unnecessary re-import or conflicts
        if py_file.name == "__init__.py":
            continue

        # Build a module path by joining the file path's components with dots
        module_path = ".".join(
            py_file.with_suffix("").relative_to(Path.cwd()).parts,
        )

        # Ensure the path to our target directory is in sys.path so it can be imported

        # Import the module using Python's importlib
        importlib.import_module(module_path)
