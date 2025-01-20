import sys
from collections.abc import Callable

import strawberry
import strawberry.tools
import strawberry.utils
import strawberry.utils.typing
from fastapi import Request, Response
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


async def fake_dl(keys: list) -> list:
    """
    A placeholder asynchronous function that simulates fetching lists of items for each key.

    This function returns an iterable of empty lists corresponding to each key.
    In actual usage, replace it with a real data loader function.

    Args:
        keys (list): A collection of keys for which data needs to be fetched.

    Returns:
        list: An iterable of empty lists corresponding to each key.
    """
    return {k: [] for k in keys}.values()


def genre_empty_query() -> object:
    """
    Generate an empty class for GraphQL queries.

    This class acts as a container for resolvers (query methods). If
    no queries are generated dynamically, this empty container is used
    to avoid schema definition errors.

    Returns:
        object: An empty class to hold query resolvers.
    """
    class Query:
        """
        A class used as a container for defining GraphQL queries.
        All resolvers associated with fetching data are attached
        to instances of this class or its subclasses.
        """
        pass

    return Query


def genre_empty_mutation() -> object:
    """
    Generate an empty class for GraphQL mutations.

    This class is used as a container for mutation resolvers (methods
    that create, update, or delete data). If no mutations are generated
    dynamically, this ensures the schema remains valid.

    Returns:
        object: An empty class to hold mutation resolvers.
    """
    class Mutation:
        __auto_generated__ = True
        """
        A class used as a container for defining GraphQL mutations. It
        contains methods that alter data state in the database, typically
        involving create, update, and delete operations.
        """

    return Mutation


async def hello_world() -> str:
    """
    A simple resolver function returning a greeting message.

    Returns:
        str: A greeting, "Hello World".
    """
    return "Hello World"


class GraphemyRouter(GraphQLRouter):
    """
    A custom router class that sets up a GraphQL API using schemas generated
    from SQLModel classes. It handles dynamic query and mutation generation,
    permissions, and context setup for each request.

    Args:
        query (object, optional): A class containing GraphQL query resolvers.
        mutation (object, optional): A class containing GraphQL mutation resolvers.
        context_getter (Callable, optional): A function to get additional context for each request.
        permission_getter (Callable, optional): A function to determine permissions for operations.
        dl_filter (Callable, optional): A function to apply filters to data loaders.
        query_filter (Callable, optional): A function to apply filters to queries.
        engine (Engine | Dict[str, Engine], optional): Database engine(s) used for SQL operations.
        extensions (list, optional): List of Strawberry extensions to be applied to the schema.
        enable_queries (bool): Flag to enable query generation. Defaults to True.
        enable_put_mutations (bool): Flag to enable PUT mutations. Defaults to False.
        enable_delete_mutations (bool): Flag to enable DELETE mutations. Defaults to False.
        auto_foreign_keys (bool): Flag to automatically handle foreign keys. Defaults to False.
        **kwargs: Additional keyword arguments passed to the base GraphQLRouter.
    """

    def __init__(
        self,
        query: object | None = None,
        mutation: object | None = None,
        context_getter: Callable | None = None,
        permission_getter: Callable | None = None,
        dl_filter: Callable | None = None,
        query_filter: Callable | None = None,
        engine: Engine | dict[str, Engine] = None,
        extensions: list | None = None,
        *,
        enable_queries: bool = True,
        enable_put_mutations: bool = False,
        enable_delete_mutations: bool = False,
        auto_foreign_keys: bool = False,
        **kwargs: dict,
    ) -> None:

        # If no extensions are specified, initialize with an empty list
        if not extensions:
            extensions = []

        # If no custom query container is provided, generate an empty one
        if not query:
            query = genre_empty_query()

        # If no custom mutation container is provided, generate an empty one
        if not mutation:
            mutation = genre_empty_mutation()

        # Dictionary to hold references to "dataloader" creation functions
        functions: dict[str, tuple] = {}

        # Configure the Setup class with engine, permission_getter, and query_filter
        Setup.setup(
            engine=engine,
            permission_getter=permission_getter,
            query_filter=query_filter,
        )

        # Flags to determine if we need fallback query and/or mutation fields
        need_query = True
        need_mutation = True

        # Iterate over all "Graphemy" classes stored in Setup.classes
        for cls in Setup.classes.values():
            # Set up the schema for each class (query, mutation, etc.)
            # This function registers fields for the generated schema.
            set_schema(cls, functions, auto_foreign_keys=auto_foreign_keys)

            # Determine whether to enable queries/mutations for this class,
            # falling back to the flags passed to GraphemyRouter if None.
            if cls.__enable_query__ is None:
                cls.__enable_query__ = enable_queries
            if cls.__enable_put_mutation__ is None:
                cls.__enable_put_mutation__ = enable_put_mutations
            if cls.__enable_delete_mutation__ is None:
                cls.__enable_delete_mutation__ = enable_delete_mutations

            # Generate query, filter, and order-by structures from the class
            cls_query, cls_filter, cls_order_by = get_query(cls)

            # Dynamically set references in the current module for convenience
            setattr(
                sys.modules[__name__],
                cls.__name__ + "Schema",
                cls.__strawberry_schema__,
            )
            setattr(
                sys.modules[__name__],
                cls.__name__ + "Filter",
                cls_filter,
            )
            setattr(
                sys.modules[__name__],
                cls.__name__ + "OrderBy",
                cls_order_by,
            )

            # If queries are enabled for this class, attach the resolver to the query container
            if cls.__enable_query__:
                need_query = False
                setattr(
                    query,
                    cls.__queryname__,
                    cls_query,
                )

            # If PUT mutations are enabled for this class, attach them to the mutation container
            if cls.__enable_put_mutation__:
                need_mutation = False
                setattr(
                    mutation,
                    "put_" + cls.__tablename__.lower(),
                    get_put_mutation(cls),
                )

            # If DELETE mutations are enabled for this class, attach them to the mutation container
            if cls.__enable_delete_mutation__:
                need_mutation = False
                setattr(
                    mutation,
                    "delete_" + cls.__tablename__.lower(),
                    get_delete_mutation(cls),
                )

        # If no queries were generated, add a fallback "hello_world" query
        if need_query:
            query.hello_world = strawberry.field(hello_world)

        # Create a context getter that sets up data loaders and merges with any custom context
        async def get_context(request: Request, response: Response) -> dict:
            """
            Generate a dictionary-based context for each request, including
            data loaders (GraphemyDataLoader) configured with optional filters
            and permission checks.

            Args:
                request (Request): Incoming FastAPI request object.
                response (Response): Outgoing FastAPI response object.

            Returns:
                dict: The context that will be passed to each GraphQL resolver.
            """
            # Either call a user-provided context_getter or use an empty dict by default
            context = (
                await context_getter(request, response)
                if context_getter
                else {}
            )

            # For each function in 'functions', create a GraphemyDataLoader.
            # If permission is denied for "query" type, use fake_dl instead.
            for k, (func, return_class) in functions.items():
                context[k] = GraphemyDataLoader(
                    load_fn=(
                        func
                        if await Setup.permission_getter(return_class, context, "query")
                        else fake_dl
                    ),
                    filter_method=dl_filter,
                    context=context,
                )
            return context

        # Build the Strawberry schema object with the generated/assigned query and mutation classes
        schema = strawberry.Schema(
            query=strawberry.type(query),
            mutation=(
                None
                # If no mutations were needed and the class is only an auto-generated stub, skip it
                if need_mutation and hasattr(mutation, "__auto_generated__")
                else strawberry.type(mutation)
            ),
            extensions=extensions,
        )

        # Initialize the parent GraphQLRouter with the schema and context getter
        super().__init__(schema=schema, context_getter=get_context, **kwargs)

    async def process_result(
        self,
        request: Request,
        result: ExecutionResult,
    ) -> GraphQLHTTPResponse:
        """
        Process the GraphQL execution result, formatting errors and managing permissions.

        Args:
            request (Request): The incoming FastAPI request object.
            result (ExecutionResult): The result from executing a GraphQL operation.

        Returns:
            GraphQLHTTPResponse: The formatted response to be returned to the client.
        """
        data: GraphQLHTTPResponse = {"data": result.data}

        # Collect all errors to be sent back in the response
        errors = []

        # If custom permission errors were accumulated, format and add them
        if hasattr(request.state, "errors"):
            errors.append(
                format_graphql_error(
                    GraphQLError(
                        "User doesn't have necessary permissions for this path",
                        path=[c.__tablename__ for c in request.state.errors],
                    ),
                ),
            )

        # Add any GraphQL execution errors that occurred during resolving
        if result.errors:
            errors.extend([format_graphql_error(err) for err in result.errors])

        # Attach the errors array to the response if any are present
        if len(errors) > 0:
            data["errors"] = errors

        # If there are any recorded 'count' fields in the request state, attach them to the response
        if hasattr(request.state, "count"):
            for fields in request.state.count:
                temp = data["data"]
                # Traverse down the path indicated by fields, then add a 'Count' key
                for _f in fields[:-1]:
                    temp = temp[_f]
                temp[fields[-1] + "Count"] = request.state.count[fields]

        # Return the fully processed response data
        return data
