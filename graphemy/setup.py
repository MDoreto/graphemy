from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar

import strawberry
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import Select
from sqlmodel import Session
from strawberry.permission import BasePermission


if TYPE_CHECKING:
    from .models import Graphemy


class Setup:
    """
    A utility class for configuring database engines (async or sync),
    permission checks, and query filtering for Graphemy-based GraphQL
    operations.
    """

    # A dictionary of named SQLAlchemy engine instances.
    # Example: {"default": sync_engine, "alternative": sync_or_async_engine}
    engine: dict[str, Engine] = None

    # A function responsible for determining whether a request
    # has permission to perform certain operations.
    permission_getter: Callable

    # Indicates if the configured engine is asynchronous.
    async_engine: bool = False

    # A dictionary to store references to Graphemy classes by name.
    classes: ClassVar[dict[str, "Graphemy"]] = {}

    @classmethod
    async def execute_query(cls, query: Select, engine: Engine) -> list:
        """
        Execute a SQL query using either an asynchronous or synchronous
        SQLAlchemy session, depending on the configured engine.

        Args:
            query (Select): The SQL query to execute.
            engine (Engine): The key name of the engine in the 'engine' dict
                or the actual engine object.

        Returns:
            list: A list of results from the executed query.
        """

        # If an asynchronous engine is configured, use an AsyncSession.
        if cls.async_engine:
            async_session = sessionmaker(
                cls.engine[engine],     # Retrieve the engine by key
                class_=AsyncSession,
                expire_on_commit=False,
            )
            async with async_session() as session:
                # Execute the provided query asynchronously
                r = await session.execute(query)
                return r.scalars().all()
        else:
            # Otherwise, use a standard synchronous session
            with Session(cls.engine[engine]) as session:
                return session.exec(query).all()

    @classmethod
    def setup(
        cls,
        engine: dict[str, Engine] | Engine,
        permission_getter: Callable | None = None,
        query_filter: Callable | None = None,
    ) -> None:
        """
        Configure the Setup class with a database engine (or engines),
        permission getter, and query filter function.

        - If a single engine is passed, it is stored under 'default'.
        - If a dict of engines is passed, each key/value becomes a named engine.
        - If the engine is async-based, 'async_engine' is set to True.

        Args:
            engine (dict[str, Engine] | Engine):
                A single SQLAlchemy engine or a dictionary of named engines.
            permission_getter (Callable | None, optional):
                A function that determines if certain operations are permitted.
                Defaults to an async function that always returns True.
            query_filter (Callable | None, optional):
                A function used to filter queries based on conditions, such as
                user permissions or contextual data. Defaults to a function
                that returns True for all queries.
        """
        # Store the engine(s). If a single engine is passed, wrap it in a dict.
        if isinstance(engine, dict):
            cls.engine = engine
        else:
            cls.engine = {"default": engine}

        # Detect if the engine is async by checking the module name
        if engine and "async" in cls.engine["default"].__module__:
            cls.async_engine = True

        # Store or create a default query filter
        if query_filter:
            cls.query_filter = query_filter
        else:
            def query_filter_default(
                _cls: "Graphemy",
                _info: strawberry.Info,
            ) -> bool:
                # Default always returns True (no filtering)
                return True

            cls.query_filter = query_filter_default

        # Store or create a default permission getter
        if permission_getter:
            cls.permission_getter = permission_getter
        else:
            async def permission_getter(
                _module_class: "Graphemy",
                _info: strawberry.Info,
                _type: str,
            ) -> bool:
                # Default always returns True (no permission checks)
                return True

            cls.permission_getter = permission_getter

    @classmethod
    async def has_permission(
        cls,
        module: "Graphemy",
        context: dict,
        request_type: str,
    ) -> bool:
        """
        Determine if a request has permission to access or modify
        a particular module (Graphemy) based on the configured
        permission_getter functions.

        Args:
            module (Graphemy): The Graphemy module/class to check permission for.
            context (dict): Typically the GraphQL context, containing
                request/response objects and potentially user info.
            request_type (str): A label describing what kind of request
                is being made (e.g., 'read', 'create', 'update', 'delete').

        Returns:
            bool: True if permission is granted, False otherwise.
        """
        # First, check the module's own permission_getter if available
        permission = await module.permission_getter(context, request_type)
        if isinstance(permission, bool):
            return permission

        # Fallback to the global permission_getter
        return await cls.permission_getter(
            module,
            context,
            request_type,
        )

    @classmethod
    def get_auth(cls, module: "Graphemy", request_type: str) -> BasePermission:
        """
        Generate a Strawberry BasePermission subclass that checks user
        permissions for a given module and request type. If permission
        is denied, it sets the HTTP status to 403 and records the module
        in the request's state.errors list.

        Args:
            module (Graphemy): The Graphemy module/class to check permission for.
            request_type (str): A label describing what kind of request
                is being made (e.g., 'read', 'create', 'update', 'delete').

        Returns:
            BasePermission: A Strawberry-compatible permission class that
            will be invoked during the GraphQL resolver flow.
        """

        class IsAuthenticated(BasePermission):
            """
            A Strawberry permission class that ensures the user or context
            has the appropriate privileges to access this module.
            """

            async def has_permission(
                self,
                _source: str,
                info: strawberry.Info,
                **_kwargs: dict,
            ) -> bool:
                """
                Check the permission by calling Setup.has_permission. If
                the permission is not granted, respond with a 403 status.
                """

                # If permission fails, set HTTP 403 and record the error.
                if not await cls.has_permission(
                    module,
                    info.context,
                    request_type,
                ):
                    info.context["response"].status_code = 403

                    # Record the module in the request's state errors
                    if not hasattr(info.context["request"].state, "errors"):
                        info.context["request"].state.errors = [module]
                    elif module not in info.context["request"].state.errors:
                        info.context["request"].state.errors.append(module)

                # Return True to avoid blocking the GraphQL flow.
                # The above steps set the status and record the error if needed.
                return True

        return IsAuthenticated