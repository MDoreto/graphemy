import glob
import inspect
import os
from typing import Annotated

import strawberry

from .models import ListFilters
from .setup import graphql_directory


def find_class_directory(class_name):
    for file_path in glob.iglob(
        f'{graphql_directory}/**/*.py', recursive=True
    ):
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
                filters: Annotated[f, strawberry.lazy('app.routers.graphql')]
                | None = None,
            ) -> Annotated[s, strawberry.lazy('app.routers.graphql')] | None:
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
                filters: Annotated[f, strawberry.lazy('app.routers.graphql')]
                | None = None,
                list_filters: ListFilters | None = None,
            ) -> list[Annotated[s, strawberry.lazy('app.routers.graphql')]]:
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
