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
    engine: dict[str, Engine] = None
    permission_getter: Callable
    async_engine: bool = False
    classes: ClassVar[dict[str, "Graphemy"]] = {}

    @classmethod
    async def execute_query(cls, query: Select, engine: Engine) -> list:
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
                _cls: "Graphemy",
                _info: strawberry.Info,
            ) -> bool:
                return True

            cls.query_filter = query_filter_default
        if permission_getter:
            cls.permission_getter = permission_getter
        else:

            async def permission_getter(
                _module_class: "Graphemy",
                _info: strawberry.Info,
                _type: str,
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
                    if not hasattr(info.context["request"].state, "errors"):
                        info.context["request"].state.errors = [module]
                    elif module not in info.context["request"].state.errors:
                        info.context["request"].state.errors.append(module)
                return True

        return IsAuthenticated
