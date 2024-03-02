import strawberry
from datetime import date

@strawberry.input
class DateFilter:
    range: list[date] | None = None
    items: list[date] | None = None
    year: int | None = None