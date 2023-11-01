import glob
import importlib.util
import inspect
import os
import sys

import strawberry
from fastapi import Request
from graphql.error import GraphQLError
from graphql.error.graphql_error import format_error as format_graphql_error
from strawberry.dataloader import DataLoader
from strawberry.fastapi import GraphQLRouter
from strawberry.http import GraphQLHTTPResponse
from strawberry.schema import BaseSchema
from strawberry.types import ExecutionResult

from .models import MyDate, MyModel
from .setup import Setup


def import_all(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                module_name = os.path.splitext(file)[0]
                print('modu', module_name)
                module_path = os.path.relpath(
                    os.path.join(root, module_name), directory
                )
                module_path = module_path.replace(os.path.sep, '.')

                importlib.import_module(module_path)


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


functions = [
    (n, f, os.path.basename(os.path.dirname(inspect.getfile(f))))
    for n, f in inspect.getmembers(sys.modules[__name__], inspect.isfunction)
    if n.startswith('dl_')
]


async def fake_dl_one(keys):
    return {k: None for k in keys}.values()


async def fake_dl_list(keys):
    return {k: [] for k in keys}.values()


class Query:
    @strawberry.field
    async def hello_word(self, info) -> str:
        return 'Hello Word'


class Mutation:
    @strawberry.mutation
    async def hello_word(self, info) -> str:
        return 'Hello Word'


# atribui as queries e mutations para as classes vazias e seta atributos de modulo para armazenas schemas e filtros


schema = strawberry.Schema(
    query=strawberry.type(Query), mutation=strawberry.type(Mutation)
)


class MyGraphQLRouter(GraphQLRouter):
    def __init__(self, query, **kwargs):
        for root, dirs, files in os.walk(Setup.folder):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    module_name = os.path.splitext(file)[0]
                    module_path = os.path.join(root, module_name)
                    module_path = os.path.relpath(
                        os.path.join(root, module_name)
                    )
                    module_path = module_path.replace(os.path.sep, '.')
                    for n, cls in [
                        (n, cls)
                        for n, cls in inspect.getmembers(
                            sys.modules[module_path], inspect.isclass
                        )
                        if issubclass(cls, MyModel)
                        and cls.__name__ != 'MyModel'
                    ]:
                        print('cls.__name__', cls.__name__)
                        setattr(
                            sys.modules[__name__],
                            cls.__name__ + 'Schema',
                            cls.schema,
                        )
                        setattr(
                            sys.modules[__name__],
                            cls.__name__ + 'Filter',
                            cls.filter,
                        )
                        print(
                            'query',
                            cls.__query__
                            if hasattr(cls, '__query__')
                            else cls.__tablename__ + 's',
                        )
                        setattr(
                            query,
                            cls.__query__
                            if hasattr(cls, '__query__')
                            else cls.__tablename__ + 's',
                            strawberry.field(
                                cls.query, permission_classes=[cls.auth]
                            ),
                        )
                        if cls._default_mutation:
                            setattr(
                                schema.mutation,
                                'put_' + cls.__tablename__.lower(),
                                strawberry.mutation(
                                    cls.mutation, permission_classes=[cls.auth]
                                ),
                            )
                        if cls._delete_mutation:
                            setattr(
                                schema.mutation,
                                'delete_' + cls.__tablename__.lower(),
                                strawberry.mutation(
                                    cls.delete_mutation,
                                    permission_classes=[cls.auth],
                                ),
                            )
        schema = strawberry.Schema(query=strawberry.type(query))
        super().__init__(schema=schema, **kwargs)

    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {'data': result.data}
        errors = []
        if 'errors' in request.scope:
            errors.append(
                format_graphql_error(
                    GraphQLError(
                        "User don't have necessary permissions for this path",
                        path=request.scope['errors'],
                    )
                )
            )
        if result.errors:
            errors.extend([format_graphql_error(err) for err in result.errors])
        if len(errors) > 0:
            data['errors'] = errors
        return data
