from collections.abc import Callable
from typing import TYPE_CHECKING

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
    """A configuration class responsible for setting up and managing database engines, executing queries,
    and facilitating permission checks for GraphQL operations.

    Attributes:
        engine (Dict[str, Engine]): A dictionary of SQLAlchemy engine instances indexed by name.
        get_permission (callable): A function to determine if a request is permitted based on
            custom business logic.
        async_engine (bool): A flag indicating if the engine configuration supports asynchronous
            operations.
        classes (Dict[str, 'Graphemy']): A registry of model classes that might be involved in GraphQL
            queries or mutations.

    """

    engine: dict[str, Engine] = None
    permission_getter: Callable
    async_engine: bool = False
    classes: dict[str, "Graphemy"] = {}

    @classmethod
    async def execute_query(cls, query: Select, engine: Engine) -> list:
        """Execute a given SQL query using the specified database engine, either asynchronously or synchronously
        based on the engine configuration.

        Args:
            query: The SQL query to be executed.
            engine (str): The key of the engine in the 'engine' attribute to be used for the query.

        Returns:
            list: The result of the query execution, typically a list of database records.

        """
        if cls.async_engine:
            async_session = sessionmaker(
                cls.engine[engine],
                class_=AsyncSession,
                expire_on_commit=False,
            )
            async with async_session() as session:
                r = await session.execute(query)
                return r.scalars().all()
        else:
            with Session(cls.engine[engine]) as session:
                return session.exec(query).all()

    @classmethod
    def setup(
        cls,
        engine: dict[str, Engine] | Engine,
        permission_getter: Callable | None = None,
        query_filter: Callable | None = None,
    ) -> None:
        """Configure the database engines and sets default functions for permission checks and query filtering.

        Args:
            engine (Dict[str, Engine] | Engine): A dictionary of engines or a single engine to be used.
            permission_getter (callable): A function to determine if a request is permitted.
            query_filter (callable): A function to filter queries based on specific conditions.

        """
        if isinstance(engine, dict):
            cls.engine = engine
        else:
            cls.engine = {"default": engine}
        if engine and "async" in cls.engine["default"].__module__:
            cls.async_engine = True
        if query_filter:
            cls.query_filter = query_filter
        else:

            def query_filter_default(
                _cls: "Graphemy", _info: strawberry.Info,
            ) -> bool:
                return True

            cls.query_filter = query_filter_default
        if permission_getter:
            cls.permission_getter = permission_getter
        else:

            async def permission_getter(
                _module_class: "Graphemy", _info: strawberry.Info, _type: str,
            ) -> bool:
                return True

            cls.permission_getter = permission_getter

    @classmethod
    async def has_permission(
        cls,
        module: "Graphemy",
        context: dict,
        request_type: str,
    ) -> bool:
        """Determine if a user has permission to execute a GraphQL query or mutation based on the
        provided context and request type.

        Args:
            module ('Graphemy'): The model class for which permissions are being checked.
            context (dict): The context of the GraphQL request.
            request_type (str): The type of request (e.g., 'query' or 'mutation') to determine the appropriate permissions.

        Returns:
            A boolean indicating if the user has permission to execute the request.

        """
        permission = await module.permission_getter(context, request_type)
        if isinstance(permission, bool):
            return permission
        return await cls.permission_getter(
            module,
            context,
            request_type,
        )

    @classmethod
    def get_auth(cls, module: "Graphemy", request_type: str) -> BasePermission:
        """Create a custom Strawberry GraphQL permission class that performs authentication and authorization checks.

        Args:
            module ('Graphemy'): The model class for which permissions are being checked.
            request_type (str): The type of request (e.g., 'query' or 'mutation') to determine the appropriate permissions.

        Returns:
            An instance of a Strawberry permission class that can be used to control access to GraphQL operations.

        """

        class IsAuthenticated(BasePermission):
            async def has_permission(
                self,
                _source: str,
                info: strawberry.Info,
                **_kwargs: dict,
            ) -> bool:
                if not await cls.has_permission(
                    module,
                    info.context,
                    request_type,
                ):
                    info.context["response"].status_code = 403
                    if "errors" not in info.context["request"].scope:
                        info.context["request"].scope["errors"] = [module]
                    elif module not in info.context["request"].scope["errors"]:
                        info.context["request"].scope["errors"].append(module)
                return True

        return IsAuthenticated
