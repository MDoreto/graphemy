from collections.abc import Callable
from types import UnionType
from typing import (
    TYPE_CHECKING,
    Annotated,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

import strawberry
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.inspection import inspect
from strawberry.tools import merge_types
from strawberry.types import Info
from strawberry.types.field import StrawberryField

from graphemy.database.operations import (
    delete_item,
    get_all,
    get_items,
    multiple_sort,
    put_item,
)
from graphemy.setup import Setup

from .models import Order, filter_models

if TYPE_CHECKING:
    from graphql.pyutils.path import Path

    from graphemy.dl import Dl
    from graphemy.models import Graphemy

T = TypeVar("T")


def set_schema(
    cls: "Graphemy",
    functions: dict[str, tuple[Callable, "Graphemy"]], *,
    auto_foreign_keys:bool = False,
) -> None:
    """Set the Strawberry schema for a Graphemy class."""

    # Define a class to hold Strawberry schema fields
    class Schema:
        pass

    foreign_keys_info = []
    for attr in [
        attr for attr in cls.__dict__.values() if hasattr(attr, "dl")
    ]:
        returned_class: Graphemy = Setup.classes[attr.dl]
        setattr(
            Schema,
            attr.__name__,
            strawberry.field(
                attr,
                permission_classes=[
                    Setup.get_auth(
                        returned_class,
                        "query",
                    ),
                ],
            ),
        )
        if attr.foreign_key or (
            attr.foreign_key is None and auto_foreign_keys and not attr.many
        ):
            source = (
                attr.source if isinstance(attr.source, list) else [attr.source]
            )
            target = (
                attr.target if isinstance(attr.target, list) else [attr.target]
            )
            target = [returned_class.__tablename__ + "." + t for t in target]

            if (
                len(source) > 0
                and len(target) > 0
                and not any(
                    isinstance(item, int)
                    or (isinstance(item, str) and item.startswith("_"))
                    for item in source + target
                )
            ):
                cls.__table__.append_constraint(
                    ForeignKeyConstraint(source, target),
                )
                foreign_keys_info.append((source, target))
        if attr.dl_name not in functions:
            functions[attr.dl_name] = (
                get_dl_field(attr, returned_class),
                returned_class,
            )
    if not cls.__strawberry_schema__:
        extra_schema = strawberry.type(
            cls.Strawberry,
            name=f"{cls.__name__}Schema2",
        )
        strawberry_schema = strawberry.experimental.pydantic.type(
            cls,
            all_fields=True,
            name=f"{cls.__name__}Schema",
        )(Schema)
        if extra_schema.__annotations__:
            strawberry_schema = merge_types(
                f"{cls.__name__}Schema",
                (strawberry_schema, extra_schema),
            )
        cls.__strawberry_schema__ = strawberry_schema


def get_dl_field(attr: callable, returned_class: "Graphemy") -> callable:
    returned_schema = returned_class.__strawberry_schema__
    if attr.many:
        returned_schema: TypeVar = list[returned_schema]

    else:
        returned_schema: TypeVar = returned_schema | None

    async def dataloader(
        keys: list[tuple],
    ) -> returned_schema:
        return await get_items(returned_class, keys, attr.target)

    dataloader.__name__ = attr.dl_name
    return dataloader


def get_path(path:"Path") -> tuple:
    if path.prev:
        return (*get_path(path.prev), path.key)
    return (path.key,)


def get_dl_function(
    field_name: str,
    field_type: "T",
    field_value: "Dl",
) -> Callable[[], Union["Graphemy", list["Graphemy"]]]:
    """Dynamically generate a DataLoader function based on the field's specifications.
    The returned function will be used by Strawberry GraphQL to lazily load related data.

    Parameters
    ----------
    field_name : str
        The name of the field for which the DataLoader function is being generated.
    field_type : T
        The Python type annotation associated with the field. This may be a list type.
    field_value : Dl
        A data structure holding metadata about the DataLoader, such as source keys, targets,
        and foreign keys.

    Returns
    -------
    Callable
        A callable DataLoader function that can be attached to a Strawberry field and invoked at runtime.

    """
    # Check if the field is a list type and extract the inner class type
    is_list = get_origin(field_type) is list
    class_type = get_args(field_type)[0] if is_list else field_type

    # Construct the DataLoader name based on the target configuration
    if isinstance(field_value.target, str):
        dl_target_name = field_value.target
    else:
        dl_target_name = "_".join(field_value.target)
    dl_name = f"dl_{class_type}_{dl_target_name}"

    # Define the return type using Strawberry's lazy type resolution
    return_type = Annotated[
        f"{class_type}Schema",
        strawberry.lazy("graphemy.router"),
    ]

    def resolve_attribute(instance:"Graphemy", attr:str | int) -> str | int:
        if isinstance(attr, int):
            return attr
        attr_name = attr[1:] if attr.startswith("_") else attr
        return getattr(instance, attr_name)

    def resolve_value(instance:"Graphemy")-> list[str|int] | str | int:
        if isinstance(field_value.source, list):
            return [
                resolve_attribute(instance, attr)
                for attr in field_value.source
            ]
        return resolve_attribute(instance, field_value.source)
    if is_list:

        async def loader_func(
            self:"Graphemy",
            info: Info,
            where: Annotated[
                f"{class_type}Filter",
                strawberry.lazy("graphemy.router"),
            ]
            | None = None,
            order_by: list[
                Annotated[
                    f"{class_type}OrderBy",
                    strawberry.lazy("graphemy.router"),
                ]
            ]
            | None = None,
            offset: int | None = None,
            limit: int | None = None,
        ) -> list[return_type]:
            value = resolve_value(self)
            result = await info.context[dl_name].load(value, where)
            if order_by:
                result = multiple_sort(
                    Setup.classes[class_type],
                    result,
                    order_by,
                )
            if offset or limit:
                if not hasattr(info.context["request"].state, "count"):
                    info.context["request"].state.count = {}
                info.context["request"].state.count[get_path(info.path)] = len(
                    result,
                )
            if offset:
                result = result[offset:]
            if limit:
                result = result[:limit]

            return result

    else:
        async def loader_func(
            self:"Graphemy",
            info: Info,
            where: Annotated[
                f"{class_type}Filter",
                strawberry.lazy("graphemy.router"),
            ]
            | None = None,
        ) -> return_type | None:
            value = resolve_value(self)
            result =  await info.context[dl_name].load(value, where)
            return result[0] if len(result)>0 else None

    # Attach custom attributes to the loader function for introspection
    loader_func.__name__ = field_name
    loader_func.dl = class_type
    loader_func.many = is_list
    loader_func.target = field_value.target
    loader_func.source = field_value.source
    loader_func.foreign_key = field_value.foreign_key
    loader_func.dl_name = dl_name

    return loader_func


def get_query(cls: "Graphemy") -> StrawberryField:
    class Filter:
        pass

    class OrderBy:
        pass

    for field_name, field in cls.__annotations__.items():
        setattr(
            OrderBy,
            field_name,
            strawberry.field(default=None, graphql_type=Order | None),
        )
        if get_origin(field) is UnionType:
            field_filter = next(
                t for t in get_args(field) if t is not type(None)
            )
        else:
            field_filter = field
        field_type = field_filter.__name__
        field_filter = (
            filter_models[field_type]
            if field_type in filter_models
            else list[field_filter]
        )
        setattr(
            Filter,
            field_type,
            strawberry.field(default=None, graphql_type=field_filter | None),
        )
    Filter.AND = strawberry.field(
        default=None,
        graphql_type=list[Filter] | None,
    )
    Filter.OR = strawberry.field(
        default=None,
        graphql_type=list[Filter] | None,
    )
    Filter.NOT = strawberry.field(
        default=None,
        graphql_type=list[Filter] | None,
    )

    filter_ = strawberry.input(name=f"{cls.__name__}Filter")(Filter)
    order_by = strawberry.input(name=f"{cls.__name__}OrderBy")(OrderBy)

    async def query(
        info: Info,
        where: filter_ | None = None,
        order_by: list[order_by] | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[cls.__strawberry_schema__]:
        if not await Setup.has_permission(cls, info.context, "query"):
            return []
        result, count = await get_all(
            cls,
            where,
            Setup.query_filter(cls, info.context),
            order_by,
            offset,
            limit,
        )
        if count is not None:
            if not hasattr(info.context["request"].state, "count"):
                info.context["request"].state.count = {}
            info.context["request"].state.count[get_path(info.path)] = count
        return result

    return (
        strawberry.field(
            query,
            permission_classes=[Setup.get_auth(cls, "query")],
        ),
        filter_,
        order_by,
    )


def get_put_mutation(cls: "Graphemy") -> StrawberryField:
    pk = [pk.name for pk in inspect(cls).primary_key]

    class Filter:
        pass

    for field_name, field in cls.__annotations__.items():
        setattr(
            Filter,
            field_name,
            strawberry.field(default=None, graphql_type=field | None),
        )
    input_schema = strawberry.input(name=f"{cls.__name__}Input")(Filter)

    async def mutation(params: input_schema) -> cls.__strawberry_schema__:
        return await put_item(cls, params, pk)

    return strawberry.mutation(
        mutation,
        permission_classes=[Setup.get_auth(cls, "mutation")],
    )


def get_delete_mutation(cls: "Graphemy") -> StrawberryField:
    pk = [pk.name for pk in inspect(cls).primary_key]

    class Filter:
        pass

    for field_name, field in cls.__annotations__.items():
        if field_name in pk:
            setattr(
                Filter,
                field_name,
                strawberry.field(default=None, graphql_type=field | None),
            )
    input_schema = strawberry.input(name=f"{cls.__name__}InputPk")(Filter)

    async def mutation(params: input_schema) -> cls.__strawberry_schema__:
        return await delete_item(cls, params, pk)

    return strawberry.mutation(
        mutation,
        permission_classes=[Setup.get_auth(cls, "delete_mutation")],
    )
