import inspect
import os
import sys
from types import GenericAlias

import strawberry
from fastapi import Request
from graphql.error import GraphQLError
from graphql.error.graphql_error import format_error as format_graphql_error
from strawberry.fastapi import GraphQLRouter
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

from .dl import MyDataLoader
from .models import MyModel
from .setup import Setup


async def fake_dl_one(keys):
    return {k: None for k in keys}.values()


async def fake_dl_list(keys):
    return {k: [] for k in keys}.values()


class MyGraphQLRouter(GraphQLRouter):
    functions = []

    def __init__(
        self,
        query,
        mutation=None,
        folder=None,
        context_getter=None,
        permission_getter=None,
        engine=None,
        **kwargs,
    ):
        functions = []
        classes = {}
        Setup.setup(engine=engine, folder=folder, get_perm=permission_getter)
        for root, dirs, files in os.walk(Setup.folder):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    module_name = os.path.splitext(file)[0]
                    module_path = os.path.join(root, module_name)
                    module_path_rel = os.path.relpath(
                        os.path.join(root, module_name)
                    )
                    module_path = module_path_rel.replace(os.path.sep, '.')
                    exec(f'import {module_path}')
                    functions.extend(
                        [
                            (
                                n,
                                f,
                                os.path.relpath(inspect.getfile(f)),
                            )
                            for n, f in inspect.getmembers(
                                sys.modules[module_path], inspect.isfunction
                            )
                            if n.startswith('dl_')
                        ]
                    )
                    for n, cls in [
                        (n, cls)
                        for n, cls in inspect.getmembers(
                            sys.modules[module_path], inspect.isclass
                        )
                        if issubclass(cls, MyModel) and n != 'MyModel'
                    ]:
                        classes[n] = (cls, module_path_rel)

        for n, (cls, path) in classes.items():
            cls.set_schema(classes)

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
            setattr(
                query,
                cls.__query__
                if hasattr(cls, '__query__')
                else cls.__tablename__ + 's',
                strawberry.field(cls.query, permission_classes=[cls.auth]),
            )
            if mutation and cls._default_mutation:
                setattr(
                    mutation,
                    'put_' + cls.__tablename__.lower(),
                    strawberry.mutation(
                        cls.mutation, permission_classes=[cls.auth]
                    ),
                )
            if mutation and cls._delete_mutation:
                setattr(
                    mutation,
                    'delete_' + cls.__tablename__.lower(),
                    strawberry.mutation(
                        cls.delete_mutation,
                        permission_classes=[cls.auth],
                    ),
                )

        async def get_context(request: Request) -> dict:
            context = context_getter(request) if context_getter else {}
            for n, f, m in functions:
                context[n] = MyDataLoader(
                    load_fn=f
                    if Setup.get_permission(m, context)
                    else fake_dl_list
                    if type(inspect.signature(f).return_annotation)
                    == GenericAlias
                    else fake_dl_one
                )
            return context

        schema = strawberry.Schema(
            query=strawberry.type(query),
            mutation=strawberry.type(mutation) if mutation else None,
        )
        super().__init__(schema=schema, context_getter=get_context, **kwargs)

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
