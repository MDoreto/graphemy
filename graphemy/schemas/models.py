from datetime import date
from enum import Enum

import strawberry


@strawberry.input
class DateFilter:
    range: list[date | None] | None = None
    items: list[date] | None = None
    year: int | None = None


@strawberry.enum
class Order(Enum):
    asc = "asc"
    desc = "desc"


@strawberry.input
class SortModel:
    field: str
    order: Order
