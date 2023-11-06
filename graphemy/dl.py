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


def dict_to_tuple(data):
    result = []
    for key, value in data.items():
        if isinstance(value, MyDate):
            value = vars(value)
        if isinstance(value, dict):
            nested_tuples = dict_to_tuple(value)
            result.append((key, nested_tuples))
        elif isinstance(value, list):
            # Substitui a lista por uma tupla antes de chamar recursivamente a função
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


def find_class_directory(class_name):
    for root, dirs, files in os.walk(Setup.folder):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as file:
                    # Verifica se a classe está definida no arquivo
                    if f'class {class_name}' in file.read():
                        return os.path.basename(os.path.dirname(file_path))
    return None


def dl(class_name=None, many=True):
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
