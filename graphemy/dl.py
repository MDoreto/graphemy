import glob
import inspect
import os

from strawberry.dataloader import DataLoader

from .models import MyDate


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


def dl(class_name: str | None = None, many: bool = True) -> callable:
    """
    Decorator for attaching metadata to a function indicating the expected behavior of a DataLoader.

    Args:
        class_name (str, optional): The data type that the DataLoader is expected to return. Defaults to None.
        many (bool, optional): Indicates whether the DataLoader should return a single item or a list of items.
            Defaults to True.

    Returns:
        callable: The decorated function.

    Example:
        >>> @dl(class_name="MyData", many=False)
        ... def load_data(item_id: int) -> dict:
        ...     # Implementation of data loading
        ...     pass

        >>> assert getattr(load_data, 'dl') == "MyData"
        >>> assert getattr(load_data, 'many') is False
    """

    def wrapper(func):
        setattr(func, 'dl', class_name)
        setattr(func, 'many', many)
        return func

    return wrapper
