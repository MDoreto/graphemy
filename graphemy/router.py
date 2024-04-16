import inspect
import sys
from types import GenericAlias
from typing import Callable, Dict

import strawberry
from fastapi import Request
from graphql.error import GraphQLError
from graphql.error.graphql_error import format_error as format_graphql_error
from sqlalchemy.engine.base import Engine
from strawberry.fastapi import GraphQLRouter
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

from .dl import GraphemyDataLoader
from .schemas.generators import (
    get_delete_mutation,
    get_put_mutation,
    get_query,
    set_schema,
)
from .setup import Setup


async def fake_dl_one(keys):
    return {k: None for k in keys}.values()


async def fake_dl_list(keys):
    return {k: [] for k in keys}.values()


class Query:
    pass


class Mutation:
    pass


async def hello_world(self, info) -> str:
    return 'Hello World'


class GraphemyRouter(GraphQLRouter):
    functions = []

    def __init__(
        self,
        query: object = Query,
        mutation: object = Mutation,
        context_getter: Callable | None = None,
        permission_getter: Callable | None = None,
        dl_filter: Callable | None = None,
        query_filter: Callable | None = None,
        engine: Engine | Dict[str, Engine] = None,
        extensions: list = [],
        enable_queries: bool = True,
        enable_put_mutations: bool = False,
        enable_delete_mutations: bool = False,
        auto_foreign_keys: bool = False,
        **kwargs,
    ):
        functions: Dict[str, tuple] = {}
        Setup.setup(
            engine=engine,
            get_perm=permission_getter,
            query_filter=query_filter,
        )
        need_query = True
        need_mutation = True
        for cls in Setup.classes.values():
            set_schema(cls, functions, auto_foreign_keys)
            if cls.__enable_query__ == None:
                cls.__enable_query__ = enable_queries
            if cls.__enable_put_mutation__ == None:
                cls.__enable_put_mutation__ = enable_put_mutations
            if cls.__enable_delete_mutation__ == None:
                cls.__enable_delete_mutation__ = enable_delete_mutations
            cls_query, cls_filter = get_query(cls)
            setattr(
                sys.modules[__name__],
                cls.__name__ + 'Schema',
                cls.__strawberry_schema__,
            )
            setattr(
                sys.modules[__name__],
                cls.__name__ + 'Filter',
                cls_filter,
            )
            if cls.__enable_query__:
                need_query = False
                setattr(
                    query,
                    cls.__queryname__,
                    cls_query,
                )
            if cls.__enable_put_mutation__:
                need_mutation = False
                setattr(
                    mutation,
                    'put_' + cls.__tablename__.lower(),
                    get_put_mutation(cls),
                )
            if cls.__enable_delete_mutation__:
                need_mutation = False
                setattr(
                    mutation,
                    'delete_' + cls.__tablename__.lower(),
                    get_delete_mutation(cls),
                )
        if need_query:
            setattr(
                query,
                'hello_world',
                strawberry.field(hello_world),
            )

        async def get_context(request: Request) -> dict:
            context = await context_getter(request) if context_getter else {}
            for k, (func, return_class) in functions.items():
                context[k] = GraphemyDataLoader(
                    load_fn=func
                    if await Setup.get_permission(
                        return_class, context, 'query'
                    )
                    else fake_dl_list
                    if type(inspect.signature(func).return_annotation)
                    == GenericAlias
                    else fake_dl_one,
                    filter_method=dl_filter,
                    request=request,
                )
            return context

        schema = strawberry.Schema(
            query=strawberry.type(query),
            mutation=None
            if need_mutation and mutation == Mutation
            else strawberry.type(mutation),
            extensions=extensions,
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
                        path=[
                            c.__tablename__ for c in request.scope['errors']
                        ],
                    )
                )
            )
        if result.errors:
            errors.extend([format_graphql_error(err) for err in result.errors])
        if len(errors) > 0:
            data['errors'] = errors
        return data
