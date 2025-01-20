from types import UnionType
from typing import TYPE_CHECKING, get_args, get_origin

from sqlalchemy import and_, not_, or_

if TYPE_CHECKING:
    from strawberry.types.base import StrawberryType
    from graphemy.models import Graphemy


def get_query_filter(
    filters_obj: "Graphemy",
    model: "Graphemy",
    query: list,
) -> list:
    """
    Build a list of SQLAlchemy boolean expressions (filters) from a nested structure
    of logical and field-level operations, appending them to the existing 'query' list.

    This function handles both logical operators (AND, OR, NOT) and field operators
    (in_, like, gt, gte, lt, lte), supporting multiple nested filter groups.

    Args:
        filters_obj (Graphemy | list[Graphemy]): A filter specification, which can
            be a single dictionary-like or list of dictionaries. Each dictionary
            can include keys for logical operators (AND, OR, NOT) or model fields
            with associated operators.
        model (Graphemy): The SQLModel-based class whose columns are being filtered.
        query (list): A list of SQLAlchemy filter expressions to which new expressions
            will be appended.

    Returns:
        list: The updated list of SQLAlchemy filter expressions.
    """
    # Ensure filters_obj is always a list for uniform handling
    filters_list = (
        filters_obj if isinstance(filters_obj, list) else [filters_obj]
    )

    # Define mappings for logical operators
    logical_ops = {
        "AND": lambda f: and_(*get_query_filter(f, model, [])),
        "OR": lambda f: or_(*get_query_filter(f, model, [])),
        "NOT": lambda f: not_(and_(*get_query_filter(f, model, []))),
    }

    # Define mappings for field-level operators
    field_ops = {
        "in_": lambda col, val: col.in_(val),
        "like": lambda col, val: col.like(val),
        "gt": lambda col, val: col > val,
        "gte": lambda col, val: col >= val,
        "lt": lambda col, val: col < val,
        "lte": lambda col, val: col <= val,
    }

    for group in filters_list:
        for op_name, op_value in group.items():
            # Skip empty values
            if not op_value:
                continue

            # If it's a logical operator (AND, OR, NOT)
            if op_name in logical_ops:
                query.append(logical_ops[op_name](op_value))
            else:
                # It's a field filter with sub-operations
                for field_op, field_val in op_value.items():
                    if field_val is not None:
                        column = getattr(model, op_name)
                        query_op = field_ops.get(field_op)
                        if query_op:
                            query.append(query_op(column, field_val))

    return query


def get_sort_criteria(
    sort: list["StrawberryType"],
    model: "Graphemy",
) -> list[tuple[str, str, str]]:
    """
    Convert a list of Strawberry-based sort definitions into a list of tuples
    usable by both SQL queries and Python-based sorting.

    Each tuple is of the form (field_name, field_type_name, order_direction).

    Args:
        sort (list[StrawberryType]): A list of objects (usually Strawberry dataclasses)
            indicating how the model should be sorted, e.g. [UserSort(field="name", order="asc")].
        model (Graphemy): The model containing annotations for each field.

    Returns:
        list[tuple[str, str, str]]: A list of sorting directives:
            (field_name, field_type_name, "asc"/"desc").
    """
    criteria = []
    for s in sort:
        # Iterate over all annotated fields in the model
        for field in model.__annotations__:
            # If the sort object doesn't specify this field, skip
            if getattr(s, field, None) is None:
                continue

            attr_type = model.__annotations__[field]

            # If the field's annotation is a UnionType, strip out None or other union components
            if get_origin(attr_type) is UnionType:
                attr_type = next(
                    t for t in get_args(attr_type) if t is not type(None)
                )

            # The 'value' attribute typically holds "asc" or "desc"
            criteria.append(
                (field, attr_type.__name__, getattr(s, field).value),
            )
    return criteria


def multiple_sort(
    model: "Graphemy",
    items: list["Graphemy"],
    sort: list["StrawberryType"],
) -> list["Graphemy"]:
    """
    Sort a list of Graphemy model instances in Python using multiple criteria.

    This is a pure Python fallback or alternative to SQL-level ordering. It can handle
    mixed field types (strings, numbers, dates/datetimes), applying ascending or descending
    orders as specified. Descending order for numeric and date-like fields is performed
    by negating the value or converting it to an inverse string.

    Args:
        model (Graphemy): The model class for the items being sorted.
        items (list[Graphemy]): A list of model instances to be sorted.
        sort (list[StrawberryType]): A list of objects indicating how sorting
            should be performed, e.g. [UserSort(field="name", order="desc")].

    Returns:
        list[Graphemy]: A new list of items sorted according to the specified criteria.
    """
    criteria = get_sort_criteria(sort, model)

    def sort_key(item: "Graphemy") -> tuple:
        key = []
        for field, field_type, order in criteria:
            value = getattr(item, field)

            # Convert date/datetime values to ordinal for numeric comparison
            if field_type in ["date", "datetime"]:
                value = value.toordinal()

            # Invert the value if descending
            if order == "desc":
                if order == "desc":
                    value = (
                        -value
                        if field_type in ["int", "float", "date", "datetime"]
                        else "".join(chr(255 - ord(c)) for c in value)
                    )
            key.append(value)
        return tuple(key)

    # Sort the items using the constructed sort_key
    return sorted(items, key=sort_key)
