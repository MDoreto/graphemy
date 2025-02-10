from datetime import date, datetime
from enum import Enum

import strawberry


@strawberry.enum
class Order(Enum):
    """
    Enum defining ascending or descending order.

    This is typically used for specifying sorting order in queries.
    """

    asc = "asc"
    desc = "desc"


@strawberry.input
class StringFilter:
    """
    Filter options for string fields.

    Fields:
        in_: Accepts a list of possible values (similar to SQL 'IN' operator).
        like: Allows pattern matching (similar to SQL 'LIKE' operator).
    """

    in_: list[str] | None = strawberry.field(name="in", default=None)
    like: str | None = None


@strawberry.input
class IntFilter:
    """
    Filter options for integer fields.

    Fields:
        in_: A list of possible values for the 'IN' filtering.
        gt: Greater than the specified value.
        gte: Greater than or equal to the specified value.
        lt: Less than the specified value.
        lte: Less than or equal to the specified value.
    """

    in_: list[int] | None = strawberry.field(name="in", default=None)
    gt: int | None = None
    gte: int | None = None
    lt: int | None = None
    lte: int | None = None


@strawberry.input
class FloatFilter:
    """
    Filter options for floating-point fields.

    Fields:
        gt: Greater than the specified value.
        gte: Greater than or equal to the specified value.
        lt: Less than the specified value.
        lte: Less than or equal to the specified value.
    """

    gt: float | None = None
    gte: float | None = None
    lt: float | None = None
    lte: float | None = None


@strawberry.input
class DateFilter:
    """
    Filter options for date fields.

    Fields:
        in_: A list of possible date values for 'IN' filtering.
        gt: Greater than the specified date.
        gte: Greater than or equal to the specified date.
        lt: Less than the specified date.
        lte: Less than or equal to the specified date.
    """

    in_: list[date] | None = strawberry.field(name="in", default=None)
    gt: date | None = None
    gte: date | None = None
    lt: date | None = None
    lte: date | None = None


@strawberry.input
class DateTimeFilter:
    """
    Filter options for datetime fields.

    Fields:
        gt: Greater than the specified datetime.
        gte: Greater than or equal to the specified datetime.
        lt: Less than the specified datetime.
        lte: Less than or equal to the specified datetime.
    """

    gt: datetime | None = None
    gte: datetime | None = None
    lt: datetime | None = None
    lte: datetime | None = None


@strawberry.input
class BoolFilter:
    """
    Filter options for boolean fields.

    Fields:
        in_: A list of possible boolean values for 'IN' filtering.
    """

    in_: list[bool] | None = strawberry.field(name="in", default=None)


# A dictionary mapping Python type names to their corresponding filter classes.
# This is used to dynamically generate filtering logic for various data types.
filter_models = {
    "str": StringFilter,
    "int": IntFilter,
    "float": FloatFilter,
    "date": DateFilter,
    "datetime": DateTimeFilter,
    "bool": BoolFilter,
}
