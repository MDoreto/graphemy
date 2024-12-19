from datetime import date, datetime
from enum import Enum

import strawberry


@strawberry.enum
class Order(Enum):
    asc = "asc"
    desc = "desc"


@strawberry.input
class StringFilter:
    in_: list[str] | None = strawberry.field(name="in", default=None)
    like: str | None = None


@strawberry.input
class IntFilter:
    in_: list[int] | None = strawberry.field(name="in", default=None)
    gt: int | None = None
    gte: int | None = None
    lt: int | None = None
    lte: int | None = None


@strawberry.input
class FloatFilter:
    gt: float | None = None
    gte: float | None = None
    lt: float | None = None
    lte: float | None = None


@strawberry.input
class DateFilter:
    in_: list[date] | None = strawberry.field(name="in", default=None)
    gt: date | None = None
    gte: date | None = None
    lt: date | None = None
    lte: date | None = None


@strawberry.input
class DateTimeFilter:
    gt: datetime | None = None
    gte: datetime | None = None
    lt: datetime | None = None
    lte: datetime | None = None


@strawberry.input
class BoolFilter:
    in_: list[bool] | None = strawberry.field(name="in", default=None)


filter_models = {
    "str": StringFilter,
    "int": IntFilter,
    "float": FloatFilter,
    "date": DateFilter,
    "datetime": DateTimeFilter,
    "bool": BoolFilter,
}
