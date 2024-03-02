from datetime import date
from typing import Optional
import strawberry
from sqlmodel import  SQLModel
from .database.operations import  get_all,put_item, delete_item
from .setup import Setup
from .schemas.generators import  get_dl_function
from .schemas.models import DateFilter
from .dl import DlModel

class Graphemy(SQLModel):
    __strawberry_schema__ = None
    _default_mutation: bool = False
    _delete_mutation: bool = False
    _disable_query: bool = False

    class Strawberry:
        pass

    def __init_subclass__(cls):
        Setup.classes[cls.__name__] = cls
        to_remove = []
        for attr_name, attr_type in cls.__annotations__.items():
            if hasattr(cls, attr_name):
                attr_value = getattr(cls, attr_name)
                if isinstance(attr_value, DlModel):
                    to_remove.append(attr_name)
                    dl_field = get_dl_function(attr_name, attr_type, attr_value)
                    setattr(cls, attr_name, dl_field)
        for attr in to_remove:
            del cls.__annotations__[attr]

    async def permission_getter(info):
        return True

    @classmethod
    def auth(cls, request_type):
        return Setup.get_auth(cls, request_type)

    @classmethod
    @property
    def filter(cls):
        if cls._filter:
            return cls._filter.default
        return None

    @classmethod
    def query(cls):
        class Filter:
            pass

        for field_name, field in cls.__annotations__.items():
            field = (
                DateFilter
                if (field == date or field == (date | None))
                else list[field]
            )
            setattr(
                Filter,
                field_name,
                strawberry.field(default=None, graphql_type=Optional[field]),
            )
        filter = strawberry.input(name=f'{cls.__name__}Filter')(Filter)
        cls._filter.default = filter

        async def field(
            self, info, filters: filter | None = None
        ) -> list[cls.schema]:
            if not await cls.permission_getter(
                info
            ) or not await Setup.get_permission(cls, info.context, 'query'):
                return []
            data = await get_all(cls, filters, Setup.query_filter(cls, info))
            return data

        return field
    
    @classmethod
    @property
    def mutation(cls):
        from sqlalchemy.inspection import inspect as insp

        pk = [pk.name for pk in insp(cls).primary_key]

        class Filter:
            pass

        for field_name, field in cls.__annotations__.items():
            setattr(
                Filter,
                field_name,
                strawberry.field(default=None, graphql_type=Optional[field]),
            )
        input = strawberry.input(name=f'{cls.__name__}Input')(Filter)

        async def mutation(self, params: input) -> cls.schema:
            return await put_item(cls, params, pk)

        return mutation

    @classmethod
    @property
    def delete_mutation(cls):
        from sqlalchemy.inspection import inspect as insp

        pk = [pk.name for pk in insp(cls).primary_key]

        class Filter:
            pass

        for field_name, field in cls.__annotations__.items():
            if field_name in pk:
                setattr(
                    Filter,
                    field_name,
                    strawberry.field(
                        default=None, graphql_type=Optional[field]
                    ),
                )
        input = strawberry.input(name=f'{cls.__name__}InputPk')(Filter)

        async def mutation(self, params: input) -> cls.schema:
            return await delete_item(cls, params, pk)

        cls._delete = mutation
        return mutation
