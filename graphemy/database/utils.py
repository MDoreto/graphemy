from types import UnionType
from typing import TYPE_CHECKING, get_args, get_origin

from sqlalchemy import and_, not_, or_

if TYPE_CHECKING:
    from strawberry.types.base import StrawberryType

    from graphemy.models import Graphemy


def get_query_filter(filters_obj:"Graphemy", model:"Graphemy", query:list) -> list:
    # Ensure filters_obj is always a list for uniform handling
    filters_list = filters_obj if isinstance(filters_obj, list) else [filters_obj]

    # Define mappings for logical operators
    logical_ops = {
        "AND": lambda f: and_(*get_query_filter(f, model, [])),
        "OR": lambda f: or_(*get_query_filter(f, model, [])),
        "NOT": lambda f: not_(and_(*get_query_filter(f, model, []))),
    }

    # Define mappings for field-level operators
    field_ops = {
        "in_":  lambda col, val: col.in_(val),
        "like": lambda col, val: col.like(val),
        "gt":   lambda col, val: col > val,
        "gte":  lambda col, val: col >= val,
        "lt":   lambda col, val: col < val,
        "lte":  lambda col, val: col <= val,
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
                # It's a field filter
                for field_op, field_val in op_value.items():
                    if field_val:
                        column = getattr(model, op_name)
                        query_op = field_ops.get(field_op)
                        if query_op:
                            query.append(query_op(column, field_val))

    return query


def multiple_sort(
    model: "Graphemy",
    items: list["Graphemy"],
    sort: list["StrawberryType"],
) -> list["Graphemy"]:
    criteria = []
    for s in sort:
        for field in model.__annotations__:
            if getattr(s, field) is None:
                continue
            attr_type = model.__annotations__[field]
            if get_origin(attr_type) is UnionType:
                attr_type = next(
                    t for t in get_args(attr_type) if t is not type(None)
                )
            criteria.append(
                (field, attr_type.__name__, getattr(s, field).value),
            )

    def sort_key(item:"Graphemy") -> tuple:
        key = []
        for field, field_type, order in criteria:
            value = getattr(item, field)
            if field_type in ["date", "datetime"]:
                value = value.toordinal()
            if order == "desc":
                value = (
                    -value
                    if field_type in ["int", "float", "date", "datetime"]
                    else "".join(chr(255 - ord(c)) for c in value)
                )
            key.append(value)
        return tuple(key)

    return sorted(items, key=sort_key)
