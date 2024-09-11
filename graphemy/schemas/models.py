from datetime import date

import strawberry


@strawberry.input
class DateFilter:
    range: list[date | None] | None = None
    items: list[date] | None = None
    year: int | None = None
