import inspect
import sys
from types import GenericAlias

import strawberry
from fastapi import Request
from graphql.error import GraphQLError
from graphql.error.graphql_error import format_error as format_graphql_error
from strawberry.fastapi import GraphQLRouter
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult
from .schemas.generators import set_schema
from .dl import MyDataLoader
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
        context_getter: callable = None,
        permission_getter: callable = None,
        dl_filter: callable = None,
        query_filter: callable = None,
        engine=None,
        extensions: list = [],
        **kwargs,
    ):
        functions = {}
        Setup.setup(
            engine=engine,
            get_perm=permission_getter,
            query_filter=query_filter,
        )
        need_query = True
        need_mutation = True
        for cls in Setup.classes.values():
            set_schema(cls, functions)
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
            if not cls._disable_query.default:
                need_query = False
                setattr(
                    query,
                    cls.__query__
                    if hasattr(cls, '__query__')
                    else cls.__tablename__ + 's',
                    strawberry.field(
                        cls.query(), permission_classes=[cls.auth('query')]
                    ),
                )
            if cls._default_mutation.default:
                need_mutation = False
                temp = strawberry.mutation(
                    cls.mutation,
                    permission_classes=[cls.auth('mutation')],
                )
                setattr(
                    mutation,
                    'put_' + cls.__tablename__.lower(),
                    temp,
                )
            if cls._delete_mutation.default:
                setattr(
                    mutation,
                    'delete_' + cls.__tablename__.lower(),
                    strawberry.mutation(
                        cls.delete_mutation,
                        permission_classes=[cls.auth('delete_mutation')],
                    ),
                )
        if need_query:
            setattr(
                query,
                'hello_world',
                strawberry.field(hello_world),
            )

        async def get_context(request: Request) -> dict:
            context = await context_getter(request) if context_getter else {}
            for k, v in functions.items():
                f = v[0]
                return_class = v[1]
                context[k] = MyDataLoader(
                    load_fn=f
                    if await Setup.get_permission(
                        return_class, context, 'query'
                    )
                    else fake_dl_list
                    if type(inspect.signature(f).return_annotation)
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
