import re
from datetime import date
from typing import TYPE_CHECKING, get_type_hints, get_origin, Optional, Union, get_args

from sqlalchemy.sql.elements import BinaryExpression
from sqlmodel import and_, bindparam, or_

if TYPE_CHECKING:
    from ..models import Graphemy
    from ..schemas.models import SortModel


def get_keys(model: "Graphemy", id: str | list[str]) -> tuple | str:
    if isinstance(id, list):
        return tuple([getattr(model, id[i]) for i in range(len(id))])
    value = getattr(model, id)
    if isinstance(value, str):
        value = value.strip()
    return value


def get_filter(
    model: "Graphemy",
    keys: tuple,
    id: str | list[str],
    params: dict,
    i: int,
) -> BinaryExpression:
    if isinstance(id, list):
        filter = []
        for j, key in enumerate(keys):
            f = []
            if None not in key:
                for k in range(len(id)):
                    f.append(
                        id[k]
                        if type(id[k]) == int
                        else (
                            id[k][1:]
                            if id[k].startswith("_")
                            else getattr(model, id[k])
                            == bindparam(
                                f"p{i}_{j}_{k}",
                                literal_execute=not isinstance(key[k], date),
                            )
                        )
                    )
                    params[f"p{i}_{j}_{k}"] = key[k]
                filter.append(and_(*f))
            else:
                filter.append(False)
        return or_(*filter)
    elif None in keys:
        keys.remove(None)
    params[f"p{i}"] = keys
    a = getattr(model, id).in_(bindparam(f"p{i}", expanding=True, literal_execute=True))
    return getattr(model, id).in_(
        bindparam(f"p{i}", expanding=True, literal_execute=True)
    )


def multiple_sort(
    model: "Graphemy", students: list["Graphemy"], sort: list["SortModel"]
) -> list["Graphemy"]:
    criteria = []
    print(model.__annotations__)
    type_hints = get_type_hints(model)
    
    # Get the field type
    for s in sort:
        if hasattr(model, s.field):
            attr = re.sub(r"(?<!^)(?=[A-Z])", "_", s.field).lower()
            field_type = type_hints.get(s.field)
    
    # Handle Optional, str | None
            if get_origin(field_type) in {Optional, Union}:
                # Extract the base type, excluding NoneType
                field_type = next(
                    arg.__name__ for arg in get_args(field_type) if arg is not type(None)
                )
            criteria.append((attr, field_type, s.order))
    print(criteria)
    def sort_key(student):
        key = []
        for field, field_type, order in criteria:
            value = getattr(student, field)
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

    return sorted(students, key=sort_key)
