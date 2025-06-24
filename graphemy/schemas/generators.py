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
    put_item,
)
from graphemy.database.utils import multiple_sort
from graphemy.setup import Setup

from .models import Order, filter_models

if TYPE_CHECKING:
    from graphql.pyutils.path import Path

    from graphemy.dl import Dl
    from graphemy.models import Graphemy

# Renamed T -> ModelType for clarity
ModelType = TypeVar("ModelType")


def set_schema(
    cls: "Graphemy",
    functions: dict[str, tuple[Callable, "Graphemy"]],
    *,
    auto_foreign_keys: bool = False,
) -> None:
    """
    Sets up a Strawberry schema for a Graphemy class, linking model fields to
    corresponding DataLoader functions, applying necessary foreign key constraints,
    and creating additional schema for Pydantic-based classes if needed.

    Args:
        cls (Graphemy): The Graphemy model class to be annotated with Strawberry fields.
        functions (dict[str, tuple[Callable, Graphemy]]): A dictionary mapping field names
            to tuples of (DataLoader function, Graphemy model).
        auto_foreign_keys (bool, optional): Whether to automatically detect and generate
            foreign key constraints for fields that do not explicitly declare them.
            Defaults to False.

    Returns:
        None
    """

    # This inner class will hold Strawberry fields for the schema
    class GraphemySchemaWrapper:
        """Wrapper class to dynamically attach Strawberry fields."""

    # Keep track of foreign key constraints we've added
    foreign_keys_added = []

    # Process each attribute in the class dict that has a `dl` attribute
    for field_attribute in [
        attr for attr in cls.__dict__.values() if hasattr(attr, "dl")
    ]:
        returned_graphemy_model: Graphemy = Setup.classes[field_attribute.dl]

        # Create a Strawberry field with permission checks
        setattr(
            GraphemySchemaWrapper,
            field_attribute.__name__,
            strawberry.field(
                field_attribute,
                permission_classes=[
                    Setup.get_auth(returned_graphemy_model, "query"),
                ], **field_attribute.to_strawberry_kwargs
            ),
        )

        # Handle foreign key constraints
        if field_attribute.foreign_key or (
            field_attribute.foreign_key is None
            and auto_foreign_keys
            and not field_attribute.many
        ):
            # Ensure we always have lists for source and target
            foreign_key_source = (
                field_attribute.source
                if isinstance(field_attribute.source, list)
                else [field_attribute.source]
            )
            foreign_key_target = (
                field_attribute.target
                if isinstance(field_attribute.target, list)
                else [field_attribute.target]
            )
            # Construct full table.column references for the target
            foreign_key_target = [
                returned_graphemy_model.__tablename__ + "." + t
                for t in foreign_key_target
            ]

            # Skip if sources or targets contain int or underscore-like placeholders
            if (
                len(foreign_key_source) > 0
                and len(foreign_key_target) > 0
                and not any(
                    isinstance(item, int)
                    or (isinstance(item, str) and item.startswith("_"))
                    for item in foreign_key_source + foreign_key_target
                )
            ):
                cls.__table__.append_constraint(
                    ForeignKeyConstraint(
                        foreign_key_source,
                        foreign_key_target,
                    ),
                )
                foreign_keys_added.append(
                    (foreign_key_source, foreign_key_target),
                )

        # Build a DataLoader function if one doesn't exist in the provided dictionary
        if field_attribute.dl_name not in functions:
            functions[field_attribute.dl_name] = (
                get_dl_field(field_attribute, field_attribute.dl),
                returned_graphemy_model,
            )

    # If the class doesn't yet have a Strawberry schema, construct one.
    if not cls.__strawberry_schema__:
        # Create an "extra" schema from the class's Strawberry attributes
        extra_schema = strawberry.type(
            cls.Strawberry,
            name=f"{cls.__name__}Schema2",
        )
        # Convert the class itself into a Strawberry-Pydantic model
        strawberry_schema = strawberry.experimental.pydantic.type(
            cls,
            all_fields=True,
            name=f"{cls.__name__}Schema",
        )(GraphemySchemaWrapper)

        # Merge both if additional fields were declared in `cls.Strawberry`
        if extra_schema.__annotations__:
            strawberry_schema = merge_types(
                f"{cls.__name__}Schema",
                (strawberry_schema, extra_schema),
            )

        # Attach the final Strawberry schema to the class
        cls.__strawberry_schema__ = strawberry_schema


def get_dl_field(
    field_attribute: Callable,
    returned_class_name: "str",
) -> Callable:
    """
    Creates a DataLoader function for a Graphemy field that may be singular or plural
    (many). This DataLoader is used to fetch related records from the database.

    Args:
        field_attribute (Callable): A function-like object that includes metadata
            about the relationship (e.g., many, target, source).
        returned_class (Graphemy): The Graphemy model that will be loaded.

    Returns:
        Callable: A function that can be registered as a DataLoader in the GraphQL
        context, responsible for fetching the correct subset of records.
    """
    # Retrieve the Strawberry schema for the related model
    related_schema = Annotated[
        f"{returned_class_name}Schema",
        strawberry.lazy("graphemy.router"),
    ]

    # If the field is many-to-many or one-to-many, the return type is a list of the schema
    if field_attribute.many:
        related_schema: ModelType = list[related_schema]
    else:
        # Else, it can be either the single schema or None
        related_schema: ModelType = related_schema | None

    async def dataloader_func(keys: list[tuple]) -> related_schema:
        """
        The underlying DataLoader function that will fetch records based on
        the `keys` which map to the source/target relationship fields.
        """
        return await get_items(
            Setup.classes[returned_class_name],
            keys,
            field_attribute.target,
        )

    dataloader_func.__name__ = field_attribute.dl_name
    return dataloader_func


def get_path(path: "Path") -> tuple:
    """
    Recursively extracts the entire GraphQL path into a tuple for logging or
    storing query counts. This helps in uniquely identifying nested field
    resolution counts.

    Args:
        path (Path): The GraphQL path object.

    Returns:
        tuple: A tuple representation of the GraphQL path.
    """
    if path.prev:
        return (*get_path(path.prev), path.key)
    return (path.key,)


def get_dl_function(
    field_name: str,
    field_type: "ModelType",
    dl_field_value: "Dl",
) -> Callable[[], Union["Graphemy", list["Graphemy"]]]:
    """
    Constructs a resolver function for a field that uses a DataLoader.

    This function handles both single-value relationships and lists,
    building the correct async resolver. It sets up special metadata
    so that later processing or introspection (e.g., in `set_schema`)
    can detect the many-to-one or one-to-many nature of the field.

    Args:
        field_name (str): The name of the field in the GraphQL schema.
        field_type (ModelType): The type annotation of the field (could be
            a single Graphemy model or a list thereof).
        dl_field_value (Dl): An object containing metadata about the target,
            source, foreign key, etc.

    Returns:
        Callable: An asynchronous resolver function to be used by the
        Strawberry field.
    """
    # Check if the field is a list
    is_list_field = get_origin(field_type) is list
    # Extract the single type if it's a list, else use the field type directly
    extracted_type = get_args(field_type)[0] if is_list_field else field_type

    # Construct a DataLoader name (e.g., dl_MyClass_MyTarget).
    if isinstance(dl_field_value.target, str):
        dl_target_name = dl_field_value.target
    else:
        dl_target_name = "_".join(dl_field_value.target)

    data_loader_name = f"dl_{extracted_type}_{dl_target_name}"

    # Set up the return type. We use Strawberry's lazy annotation for cyclical imports.
    # For example, "MyClassSchema" might be built in graphemy.router.
    return_type = Annotated[
        f"{extracted_type}Schema",
        strawberry.lazy("graphemy.router"),
    ]

    def _resolve_attribute(
        instance: "Graphemy",
        attribute: str | int,
    ) -> str | int:
        """Safely resolves an attribute (potentially prefixed with underscores) from a model instance."""
        attr_name = (
            attribute
            if isinstance(attribute, int)
            else attribute[1:]
            if attribute.startswith("_")
            else attribute
        )
        return getattr(instance, attr_name)

    def _resolve_value(instance: "Graphemy") -> list[str | int] | str | int:
        """
        Resolves the source value(s) from the instance. If the Dl source is a list,
        it collects all corresponding attributes. Otherwise, returns a single value.
        """
        if isinstance(dl_field_value.source, list):
            return [
                _resolve_attribute(instance, src_attr)
                for src_attr in dl_field_value.source
            ]
        return _resolve_attribute(instance, dl_field_value.source)

    if is_list_field:
        # Resolver for a list field
        async def loader_func(
            self: "Graphemy",
            info: Info,
            where: Annotated[
                f"{extracted_type}Filter",
                strawberry.lazy("graphemy.router"),
            ]
            | None = None,
            order_by: list[
                Annotated[
                    f"{extracted_type}OrderBy",
                    strawberry.lazy("graphemy.router"),
                ]
            ]
            | None = None,
            offset: int | None = None,
            limit: int | None = None,
        ) -> list[return_type]:
            """
            Loads multiple related items, optionally filtered, ordered, and paginated.
            """
            key_values = _resolve_value(self)
            result = await info.context[data_loader_name].load(
                key_values,
                where,
            )

            # Apply multiple sort if specified
            if order_by:
                result = multiple_sort(
                    Setup.classes[extracted_type],
                    result,
                    order_by,
                )

            # Store total count in the request state if offset/limit is used
            if offset or limit:
                if not hasattr(info.context["request"].state, "count"):
                    info.context["request"].state.count = {}
                info.context["request"].state.count[get_path(info.path)] = len(
                    result,
                )

            # Apply pagination
            if offset:
                result = result[offset:]
            if limit:
                result = result[:limit]
            return result

    else:
        # Resolver for a single field
        async def loader_func(
            self: "Graphemy",
            info: Info,
            where: Annotated[
                f"{extracted_type}Filter",
                strawberry.lazy("graphemy.router"),
            ]
            | None = None,
        ) -> return_type | None:
            """
            Loads a single related item (or None if not found).
            """
            key_values = _resolve_value(self)
            result = await info.context[data_loader_name].load(
                key_values,
                where,
            )
            return result[0] if len(result) > 0 else None

    # Attach metadata to the resolver function for introspection
    loader_func.__name__ = field_name
    loader_func.dl = extracted_type
    loader_func.many = is_list_field
    loader_func.target = dl_field_value.target
    loader_func.source = dl_field_value.source
    loader_func.foreign_key = dl_field_value.foreign_key
    loader_func.dl_name = data_loader_name
    loader_func.to_strawberry_kwargs = dl_field_value.to_strawberry_kwargs

    return loader_func


def get_query(cls: "Graphemy") -> StrawberryField:
    """
    Constructs a Strawberry query field for a given Graphemy model.
    It automatically sets up filtering, ordering, and pagination arguments,
    returning a list of items of the model.

    Args:
        cls (Graphemy): The Graphemy model for which to build a query field.

    Returns:
        StrawberryField: A Strawberry field function that can be used in a schema
        to query a list of this model.
    """

    # Dynamic classes to hold filter and order_by fields
    class Filter:
        """Dynamic input class for filters."""

    class OrderBy:
        """Dynamic input class for ordering fields."""

    # Populate Filter and OrderBy with model fields
    for field_name, field_type in cls.__annotations__.items():
        # Add ordering for each field
        setattr(
            OrderBy,
            field_name,
            strawberry.field(default=None, graphql_type=Order | None),
        )

        # If the field is annotated as a Union that includes None, extract the non-None type
        if get_origin(field_type) is UnionType:
            non_none_type = next(
                t for t in get_args(field_type) if t is not type(None)
            )
        else:
            non_none_type = field_type

        # Use existing filter models if available, else use a list-based filter
        filter_model = (
            filter_models.get(non_none_type.__name__)
            if hasattr(non_none_type, "__name__")
            and non_none_type.__name__ in filter_models
            else list[non_none_type]
        )

        setattr(
            Filter,
            field_name,
            strawberry.field(default=None, graphql_type=filter_model | None),
        )

    # Logical operators for complex filtering
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

    # Create Strawberry input types
    filter_input = strawberry.input(name=f"{cls.__name__}Filter")(Filter)
    order_by_input = strawberry.input(name=f"{cls.__name__}OrderBy")(OrderBy)

    async def query_function(
        info: Info,
        where: filter_input | None = None,
        order_by: list[order_by_input] | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[cls.__strawberry_schema__]:
        """
        The actual query resolver that fetches items from the database based on
        the provided filter, order_by, offset, and limit parameters.
        """
        # Check permissions
        if not await Setup.has_permission(cls, info.context, "query"):
            return []

        # Fetch results (and total count) from a general-purpose database operation
        result, total_count = await get_all(
            cls,
            where,
            Setup.query_filter(cls, info.context),
            order_by,
            offset,
            limit,
        )

        # Store the total count in request state if it's provided
        if total_count is not None:
            if not hasattr(info.context["request"].state, "count"):
                info.context["request"].state.count = {}
            info.context["request"].state.count[get_path(info.path)] = (
                total_count
            )

        return result

    return (
        strawberry.field(
            query_function,
            permission_classes=[Setup.get_auth(cls, "query")],
        ),
        filter_input,
        order_by_input,
    )


def get_put_mutation(cls: "Graphemy") -> StrawberryField:
    """
    Constructs a Strawberry mutation field for upserting a Graphemy model instance.
    It builds an input type from the model fields, allowing partial or full updates
    based on the model's primary key.

    Args:
        cls (Graphemy): The Graphemy model for which to build the mutation field.

    Returns:
        StrawberryField: A Strawberry mutation field that can be used to create or update
        instances of this model.
    """
    # Identify primary key fields
    primary_keys = [key.name for key in inspect(cls).primary_key]

    class InputData:
        """Dynamic input class for upsert mutation."""

    # Build the input type fields from the model's annotations
    for field_name, field_type in cls.__annotations__.items():
        setattr(
            InputData,
            field_name,
            strawberry.field(default=None, graphql_type=field_type | None),
        )

    # Create a Strawberry input class
    input_schema = strawberry.input(name=f"{cls.__name__}Input")(InputData)

    async def mutation_function(
        params: input_schema,
    ) -> cls.__strawberry_schema__:
        """
        Upserts an item in the database, inserting if it doesn't exist or updating if it does.
        """
        return await put_item(cls, params, primary_keys)

    # Return a Strawberry mutation
    return strawberry.mutation(
        mutation_function,
        permission_classes=[Setup.get_auth(cls, "mutation")],
    )


def get_delete_mutation(cls: "Graphemy") -> StrawberryField:
    """
    Constructs a Strawberry mutation field for deleting a Graphemy model instance.
    It builds an input type from the model's primary key fields.

    Args:
        cls (Graphemy): The Graphemy model for which to build the mutation field.

    Returns:
        StrawberryField: A Strawberry mutation field that can be used to delete
        instances of this model by their primary key(s).
    """
    # Identify primary key fields
    primary_keys = [key.name for key in inspect(cls).primary_key]

    class PrimaryKeyInput:
        """Dynamic input class for delete mutation, containing only primary key fields."""

    # Build input fields for primary keys
    for field_name, field_type in cls.__annotations__.items():
        if field_name in primary_keys:
            setattr(
                PrimaryKeyInput,
                field_name,
                strawberry.field(default=None, graphql_type=field_type | None),
            )

    # Create a Strawberry input class
    input_schema = strawberry.input(name=f"{cls.__name__}InputPk")(
        PrimaryKeyInput,
    )

    async def mutation_function(
        params: input_schema,
    ) -> cls.__strawberry_schema__:
        """
        Deletes an item from the database by its primary key, returning the deleted item.
        """
        return await delete_item(cls, params, primary_keys)

    # Return a Strawberry mutation
    return strawberry.mutation(
        mutation_function,
        permission_classes=[Setup.get_auth(cls, "delete_mutation")],
    )
