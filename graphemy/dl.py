import glob
import inspect
import os
from typing import Annotated

import strawberry
from strawberry.dataloader import DataLoader

from .models import ListFilters, MyDate
from .setup import Setup


class MyDataLoader(DataLoader):
    async def load(self, keys, filters: dict | None = False):
        if filters == False:
            return await super().load(keys)
        filters['keys'] = (
            tuple(keys)
            if isinstance(keys, list)
            else keys.strip()
            if isinstance(keys, str)
            else keys
        )
        return await super().load(dict_to_tuple(filters))


def dict_to_tuple(data: dict) -> tuple:
    """
    Recursively converts a nested dictionary to a sorted tuple of key-value pairs.

    This function takes a dictionary as input and recursively traverses it, converting
    it into a sorted tuple of key-value pairs. If nested dictionaries or lists are
    encountered, they are also recursively converted into sorted tuples. The final
    result is a sorted tuple of all key-value pairs in the input dictionary.

    Args:
        data (dict): The input dictionary to be converted.

    Returns:
        tuple: A sorted tuple of key-value pairs from the input dictionary.

    Example:
        >>> data = {
        ...     'name': 'John',
        ...     'age': 30,
        ...     'address': {
        ...         'street': '123 Main St',
        ...         'city': 'Exampleville'
        ...     }
        ... }
        >>> dict_to_tuple(data)
        (('address', (('city', 'Exampleville'), ('street', '123 Main St'))), ('age', 30), ('name', 'John'))

    Note:
        This function is compatible with dictionaries that contain nested dictionaries,
        lists, and instances of 'MyDate' objects. Lists are converted to sorted tuples
        before further processing.

    See Also:
        - MyDate: An example custom data type that can be converted into a dictionary.

    """
    result = []
    for key, value in data.items():
        if isinstance(value, MyDate):
            value = vars(value)
        if isinstance(value, dict):
            nested_tuples = dict_to_tuple(value)
            result.append((key, nested_tuples))
        elif isinstance(value, list):
            # Substitutes the list with a tuple before recursively calling the function
            nested_tuples = tuple(
                sorted(
                    dict_to_tuple(item)
                    if isinstance(item, dict) or isinstance(item, MyDate)
                    else item
                    for item in value
                )
            )
            result.append((key, nested_tuples))
        else:
            result.append((key, value))
    return tuple(sorted(result))


def find_class_directory(class_name: str) -> str | None:
    """
    Find the directory containing a Python class definition by class name.

    This function searches for a Python class definition in the project's source files
    and returns the relative path to the directory containing the class definition
    if found. If the class is not found in any of the source files, it returns `None`.

    Args:
        class_name (str): The name of the class to search for.

    Returns:
        str | None: The relative path to the directory containing the class definition
        if found, or `None` if the class is not found.

    Note:
        - This function searches for class definitions in Python source files (`.py`)
          within the project's directory.
        - It performs a case-sensitive search for the class name, so ensure the name
          matches exactly.
        - If multiple class definitions with the same name exist in different files,
          this function returns the first match found.
        - If no matching class is found, it returns `None`.

    See Also:
        - os: The Python 'os' module is used to traverse the project directory and
          locate source files.
        - Setup: The 'Setup' object is used to define the project setup, including
          the folder where source files are located.

    """
    for root, dirs, files in os.walk(os.path.join(os.getcwd(), Setup.folder)):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as file:
                    # Check if the class is defined in the file
                    if f'class {class_name}' in file.read():
                        return os.path.relpath(file_path)
    return None


def dl(class_name: str | None = None, many: bool = True):
    """
    Data Loader (DL) decorator for GraphQL resolvers.

    This decorator is used to define data loader functions for GraphQL resolvers. It
    allows you to specify the class name and whether the resolver handles many items
    (a list) or a single item. It also automatically associates the resolver with the
    corresponding data loader.

    Args:
        class_name (str | None, optional): The name of the class associated with the
            data loader. If not provided, the decorator will attempt to determine the
            class name based on the resolver's module. Defaults to None.
        many (bool, optional): Set to True if the resolver handles multiple items (list),
            or False for a single item. Defaults to True.

    Returns:
        function: A decorated version of the GraphQL resolver function that includes
        data loader handling.

    Example:
        To decorate a resolver for fetching a list of items:
        ```python
        @dl(class_name="MyItem", many=True)
        async def resolve_my_items(self, info, filters):
            # Resolver logic here
        ```

        To decorate a resolver for fetching a single item:
        ```python
        @dl(class_name="MyItem", many=False)
        async def resolve_my_item(self, info, filters):
            # Resolver logic here
        ```

    Note:
        - The decorator automatically associates the decorated resolver function with
          the corresponding data loader based on the provided class_name or module.
        - It also adds attributes 'dl' and 'module' to the decorated function to
          indicate that it is a data loader function and specify the associated module.
        - For single item resolvers, the function's return type should be annotated as a
          single item, while for many item resolvers, it should be annotated as a list of
          items.

    See Also:
        - find_class_directory: A function used to find the directory containing the
          class definition based on the provided class_name.
    """

    def wrapper(func):
        if not class_name:
            module = os.path.basename(
                os.path.dirname(os.path.abspath(inspect.getfile(func)))
            )
        else:
            module = find_class_directory(class_name)
        if not class_name:
            setattr(func, 'dl', True)
            setattr(func, 'module', module)
            return func
        f = class_name + 'Filter'
        s = class_name + 'Schema'
        if not many:

            async def new_func(
                self,
                info,
                filters: Annotated[f, strawberry.lazy('graphemy.router')]
                | None = None,
            ) -> Annotated[s, strawberry.lazy('graphemy.router')] | None:
                return await func(
                    self,
                    info,
                    {
                        'filters': vars(filters) if filters else None,
                        'list_filters': None,
                    },
                )

        else:

            async def new_func(
                self,
                info,
                filters: Annotated[f, strawberry.lazy('graphemy.router')]
                | None = None,
                list_filters: ListFilters | None = None,
            ) -> list[Annotated[s, strawberry.lazy('graphemy.router')]]:
                return await func(
                    self,
                    info,
                    {
                        'filters': vars(filters) if filters else None,
                        'list_filters': vars(list_filters)
                        if list_filters
                        else None,
                    },
                )

        setattr(new_func, 'dl', True)
        setattr(new_func, 'module', module)
        new_func.__name__ = func.__name__
        return new_func

    return wrapper
