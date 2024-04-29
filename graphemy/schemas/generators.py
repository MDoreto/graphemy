from datetime import date
from typing import (
    TYPE_CHECKING,
    Annotated,
    Callable,
    Dict,
    Optional,
    Tuple,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

import strawberry
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.inspection import inspect
from strawberry.field import StrawberryField
from strawberry.tools import merge_types
from strawberry.types import Info

from ..database.operations import delete_item, get_all, get_items, put_item
from ..dl import Dl
from ..setup import Setup
from .models import DateFilter

if TYPE_CHECKING:
    from ..models import Graphemy

T = TypeVar('T')


def set_schema(
    cls: 'Graphemy',
    functions: Dict[str, Tuple[Callable, 'Graphemy']],
    auto_foreign_keys,
) -> None:
    """Set the Strawberry schema for a Graphemy class."""

    # Define a class to hold Strawberry schema fields
    class Schema:
        pass

    foreign_keys_info = []
    for attr in [
        attr for attr in cls.__dict__.values() if hasattr(attr, 'dl')
    ]:
        returned_class: 'Graphemy' = Setup.classes[attr.dl]
        setattr(
            Schema,
            attr.__name__,
            strawberry.field(
                attr,
                permission_classes=[
                    Setup.get_auth(
                        returned_class,
                        'query',
                    )
                ],
            ),
        )
        if attr.foreign_key or (
            attr.foreign_key == None and auto_foreign_keys and not attr.many
        ):
            source = (
                attr.source if isinstance(attr.source, list) else [attr.source]
            )
            target = (
                attr.target if isinstance(attr.target, list) else [attr.target]
            )
            target = [returned_class.__tablename__ + '.' + t for t in target]
            cls.__table__.append_constraint(
                ForeignKeyConstraint(source, target)
            )
            foreign_keys_info.append((source, target))
        if not attr.dl_name in functions:
            functions[attr.dl_name] = (
                get_dl_field(attr, returned_class),
                returned_class,
            )
    extra_schema = strawberry.type(
        cls.Strawberry, name=f'{cls.__name__}Schema2'
    )
    strawberry_schema = strawberry.experimental.pydantic.type(
        cls, all_fields=True, name=f'{cls.__name__}Schema'
    )(Schema)
    if extra_schema.__annotations__:
        strawberry_schema = merge_types(
            f'{cls.__name__}Schema', (strawberry_schema, extra_schema)
        )
    cls.__strawberry_schema__ = strawberry_schema


def get_dl_field(attr, returned_class: 'Graphemy') -> callable:
    returned_schema = returned_class.__strawberry_schema__
    if attr.many:
        returned_schema = list[returned_schema]
    else:
        returned_schema = Optional[returned_schema]

    async def dataloader(
        keys: list[tuple],
    ) -> returned_schema:
        return await get_items(returned_class, keys, attr.target, attr.many)

    dataloader.__name__ = attr.dl_name
    return dataloader


def get_dl_function(
    field_name: str,
    field_type: T,
    field_value: Dl,
) -> Callable[[], Union['Graphemy', list['Graphemy']]]:
    """Generates a DataLoader function dynamically based on the field's specifications."""
    # Determine if the field_type is a list and extract the inner type
    is_list = get_origin(field_type) == list
    class_type = get_args(field_type)[0] if is_list else field_type

    # Formulate DataLoader name with consideration for lazy-loaded types
    dl_name = (
        field_value.target
        if isinstance(field_value.target, str)
        else '_'.join(field_value.target)
    )
    dl_name = f'dl_{class_type}_{dl_name}'

    # Define the return type using Strawberry's lazy type resolution
    return_type = Annotated[
        f'{class_type}Schema',
        strawberry.lazy('graphemy.router'),
    ]
    if is_list:
        return_type = list[return_type]

    else:
        return_type = Optional[return_type]

    async def loader_func(
        self,
        info: Info,
        filters: Annotated[
            f'{class_type}Filter',
            strawberry.lazy('graphemy.router'),
        ]
        | None = None,
    ) -> return_type:
        """The dynamically generated DataLoader function."""
        filter_args = vars(filters) if filters else None
        source_value = (
            [getattr(self, attr) for attr in field_value.source]
            if isinstance(field_value.source, list)
            else getattr(self, field_value.source)
        )
        return await info.context[dl_name].load(
            source_value, {'filters': filter_args}
        )

    # Customize the function attributes for introspection or other purposes
    loader_func.__name__ = field_name
    loader_func.dl = class_type
    loader_func.many = is_list
    loader_func.target = field_value.target
    loader_func.source = field_value.source
    loader_func.foreign_key = field_value.foreign_key
    loader_func.dl_name = dl_name

    return loader_func


def get_query(cls: 'Graphemy') -> StrawberryField:
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

    async def query(
        self, info: Info, filters: filter | None = None
    ) -> list[cls.__strawberry_schema__]:
        if not await cls.permission_getter(
            info
        ) or not await Setup.get_permission(cls, info.context, 'query'):
            return []
        data = await get_all(cls, filters, Setup.query_filter(cls, info))
        return data

    return (
        strawberry.field(
            query, permission_classes=[Setup.get_auth(cls, 'query')]
        ),
        filter,
    )


def get_put_mutation(cls: 'Graphemy') -> StrawberryField:

    pk = [pk.name for pk in inspect(cls).primary_key]

    class Filter:
        pass

    for field_name, field in cls.__annotations__.items():
        setattr(
            Filter,
            field_name,
            strawberry.field(default=None, graphql_type=Optional[field]),
        )
    input = strawberry.input(name=f'{cls.__name__}Input')(Filter)

    async def mutation(self, params: input) -> cls.__strawberry_schema__:
        return await put_item(cls, params, pk)

    return strawberry.mutation(
        mutation,
        permission_classes=[Setup.get_auth(cls, 'mutation')],
    )


def get_delete_mutation(cls: 'Graphemy') -> StrawberryField:
    pk = [pk.name for pk in inspect(cls).primary_key]

    class Filter:
        pass

    for field_name, field in cls.__annotations__.items():
        if field_name in pk:
            setattr(
                Filter,
                field_name,
                strawberry.field(default=None, graphql_type=Optional[field]),
            )
    input = strawberry.input(name=f'{cls.__name__}InputPk')(Filter)

    async def mutation(self, params: input) -> cls.__strawberry_schema__:
        return await delete_item(cls, params, pk)

    return strawberry.mutation(
        mutation,
        permission_classes=[Setup.get_auth(cls, 'delete_mutation')],
    )
