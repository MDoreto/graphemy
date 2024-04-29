This module provides a utility function to dynamically import all Python files in a given directory,
excluding `__init__.py`. It is designed to be used in applications where automatic module loading
is required, such as loading models or configurations dynamically in a web application framework.

Functions:
    import_files: Recursively imports all Python files from the specified directory path into
    the current namespace, excluding `__init__.py` files.

Details:
    - The function walks through the directory tree starting from the specified path.
    - Each Python file found (that isn't `__init__.py`) is dynamically imported.
    - Imports are done relative to the directory where the script is run, adjusting for
      package hierarchy as necessary.

::: __init__