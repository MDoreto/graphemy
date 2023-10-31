import inspect
import os
from datetime import date
from typing import Optional

import strawberry
from sqlmodel import SQLModel
from strawberry.permission import BasePermission

from .services import delete_item, get_all, put_item


@strawberry.input
class ListFilters:
    field: str
    asc: bool


def get_auth(module):
    class IsAuthenticated(BasePermission):
        message = 'User is not authenticated'
        # This method can also be async!
        async def has_permission(self, source, info, **kwargs) -> bool:
            if (
                module != 'employee'
                and module not in info.context['user'].scopes
            ):
                info.context['response'].status_code = 403
                if not 'errors' in info.context['request'].scope:
                    info.context['request'].scope['errors'] = [module]
                elif not module in info.context['request'].scope['errors']:
                    info.context['request'].scope['errors'].append(module)
            return True

    return IsAuthenticated


@strawberry.input
class MyDate:
    range: list[date] | None = None
    items: list[date] | None = None
    year: int | None = None


class MyModel(SQLModel):
    _schema = None
    _filter = None
    _query = None
    _mutation = None
    _delete = None
    _input = None
    _default_mutation = False
    __customfields__ = {}
    _default_mutation = False
    _delete_mutation = False

    @classmethod
    @property
    def auth(cls):
        folder = os.path.basename(
            os.path.dirname(os.path.abspath(inspect.getfile(cls)))
        )
        return get_auth(folder)

    @classmethod
    @property
    def filter(cls):
        if not cls._filter:

            class Filter:
                pass

            for field_name, field in cls.__annotations__.items():
                field = (
                    MyDate
                    if (field == date or field == (date | None))
                    else list[field]
                )
                setattr(
                    Filter,
                    field_name,
                    strawberry.field(
                        default=None, graphql_type=Optional[field]
                    ),
                )
            cls._filter = strawberry.input(name=f'{cls.__name__}Filter')(
                Filter
            )
        return cls._filter

    @classmethod
    @property
    def schema(cls):
        if not cls._schema:
            if cls.__tablename__ != 'employee':

                class Schema:
                    pass

            else:

                class Schema:
                    ms_token: strawberry.Private[str]
                    scopes: list[str]

            for funcao in [
                func for func in cls.__dict__.values() if hasattr(func, 'dl')
            ]:
                setattr(
                    Schema,
                    funcao.__name__,
                    strawberry.field(
                        funcao, permission_classes=[get_auth(funcao.module)]
                    ),
                )
            cls._schema = strawberry.experimental.pydantic.type(
                cls, all_fields=True, name=f'{cls.__name__}Schema'
            )(Schema)
        return cls._schema

    @classmethod
    @property
    def query(cls):
        if not cls._query:
            folder = os.path.basename(
                os.path.dirname(os.path.abspath(inspect.getfile(cls)))
            )

            async def field(
                self, info, filters: cls.filter | None = None
            ) -> list[cls.schema]:
                if not folder in info.context['user'].scopes:
                    return []
                return await get_all(cls, filters)

            cls._query = field
        return cls._query

    @classmethod
    @property
    def input(cls):
        if not cls._input:

            class Filter:
                pass

            for field_name, field in cls.__annotations__.items():
                setattr(
                    Filter,
                    field_name,
                    strawberry.field(
                        default=None, graphql_type=Optional[field]
                    ),
                )
            cls._input = strawberry.input(name=f'{cls.__name__}Input')(Filter)
        return cls._input

    @classmethod
    @property
    def mutation(cls):
        from sqlalchemy.inspection import inspect as insp

        pk = [pk.name for pk in insp(cls).primary_key]
        if not cls._mutation:

            async def mutation(self, params: cls.input) -> cls.schema:
                return await put_item(cls, params, pk)

            cls._mutation = mutation
        return cls._mutation

    @classmethod
    @property
    def delete_mutation(cls):
        from sqlalchemy.inspection import inspect as insp

        pk = [pk.name for pk in insp(cls).primary_key]
        if not cls._delete:

            async def mutation(self, params: cls.input) -> cls.schema:
                return await delete_item(cls, params, pk)

            cls._delete = mutation
        return cls._delete
