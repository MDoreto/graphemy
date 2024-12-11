from datetime import date, datetime
from enum import Enum

import strawberry

@strawberry.enum
class Order(Enum):
    asc = "asc"
    desc = "desc"


@strawberry.input
class SortModel:
    field: str
    order: Order

@strawberry.input
class StringFilter:
    regex: str | None = None
    in_: list[str] | None = strawberry.field(name="in", default_factory=None)
    nin: list[str] | None = None
    inc: list[str] | None = None
    ninc: list[str] | None = None

@strawberry.input
class IntFilter:
    in_: list[int] | None = strawberry.field(name="in", default_factory=None)
    nin: list[int] | None = None
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
    in_: list[date] | None = strawberry.field(name="in", default_factory=None)
    nin: list[date] | None = None
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

filters = { "str": StringFilter, "int": IntFilter, "float": FloatFilter, "date": DateFilter, "datetime": DateTimeFilter }