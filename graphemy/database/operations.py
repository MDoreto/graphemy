from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, and_, extract, or_, select, not_

from graphemy.schemas.models import DateFilter
from graphemy.setup import Setup

from .utils import get_filter, get_keys, multiple_sort

if TYPE_CHECKING:
    from graphemy.models import Graphemy
    from graphemy.schemas.models import SortModel


async def get_items(
    model: "Graphemy",
    parameters: list[tuple],
    id: str | list[str] = "id",
    many: bool = True,
):
    groups = {}
    id_groups = {}
    filters = {}
    params = {}
    for p in parameters:
        f = p[0]
        if f not in filters:
            filters[f] = []
        filters[f].append(p[1][1])
        groups[p] = [] if many else None
        if p[1][1] not in id_groups:
            id_groups[p[1][1]] = []
        id_groups[p[1][1]].append(p)
    query = select(model)
    query_filters = []
    for i, f in enumerate(filters):
        if f[1]:
            filter_temp = []
            for k, v in f[1]:
                if v:
                    if isinstance(v[0], tuple):
                        if v[2][1]:
                            filter_temp.append(
                                extract("year", getattr(model, k)) == v[2][1],
                            )
                        if v[0][1]:
                            filter_temp.append(
                                getattr(model, k).in_(list(v[0][1])),
                            )
                        if v[1][1] and v[1][1][0]:
                            filter_temp.append(getattr(model, k) >= v[1][1][0])
                        if v[1][1] and v[1][1][1]:
                            filter_temp.append(getattr(model, k) <= v[1][1][1])
                    else:
                        filter_temp.append(getattr(model, k).in_(v))
        else:
            filter_temp = [True]

        query_filters.append(
            and_(*filter_temp, get_filter(model, filters[f], id, params, i)),
        )
    results = await Setup.execute_query(
        query.where(or_(*query_filters)).params(**params),
        model.__enginename__,
    )
    for r in results:
        temp = id_groups[get_keys(r, id)]

        if len(temp) == 1:
            key = temp[0]
            if many:
                groups[key].append(r)
            else:
                groups[key] = r
        else:
            for t in temp:
                if not t[0][1] or all(
                    getattr(r, k) in v for k, v in t[0][1] if v
                ):
                    if many:
                        groups[t].append(r)
                    else:
                        groups[t] = r
    return groups.values()


def get_query_filter(filters_obj, model, query):
    value = filters_obj if isinstance(filters_obj, list) else [filters_obj]
    for item in value:
        filters = vars(item)
        for filter in filters:
            if not getattr(item, filter):
                continue
            if filter == 'AND':
                query.append(and_(*get_query_filter(getattr(item, filter), model, [])))
            elif filter == 'OR':
                query.append(or_(*get_query_filter(getattr(item, filter), model, [])))
            elif filter == 'NOT':
                query.append(not_(and_(*get_query_filter(getattr(item, filter), model, []))))
            else:
                field_obj = getattr(item, filter)
                field = vars(field_obj)
                for key in field:
                    if not getattr(field_obj, key):
                        continue
                    if key == 'in_':
                        query.append(getattr(model, filter).in_(field[key]))
                    elif key == 'like':
                        query.append(getattr(model, filter).like(field[key]))
                    elif key == 'gt':
                        query.append(getattr(model, filter) > field[key])
                    elif key == 'gte':
                        query.append(getattr(model, filter) >= field[key])
                    elif key == 'lt':
                        query.append(getattr(model, filter) < field[key])
                    elif key == 'lte':
                        query.append(getattr(model, filter) <= field[key])
    return query

async def get_all(
    model: "Graphemy",
    filters,
    query_filter,
    sort: list["SortModel"] | None = None,
) -> list:
    query = select(model).where(query_filter)
    if filters:
        query = query.where(*get_query_filter(filters, model, []))
    r = await Setup.execute_query(query, model.__enginename__)
    if sort and len(sort) > 0:
        r = multiple_sort(model, r, sort)
    return r


async def put_item(model: "Graphemy", item, id="id"):
    id = [getattr(item, i) for i in id]
    kwargs = vars(item)
    engine = Setup.engine[model.__enginename__]
    if Setup.async_engine:
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with async_session() as session:
            if not id or None in id:
                new_item = model(**kwargs)
            else:
                new_item = await session.get(model, id)
                if not new_item:
                    new_item = model(**kwargs)
                for key, value in kwargs.items():
                    setattr(new_item, key, value)
            session.add(new_item)
            await session.commit()
            await session.refresh(new_item)
    else:
        with Session(engine) as session:
            if not id or None in id:
                new_item = model(**kwargs)
            else:
                new_item = session.get(model, id)
                if not new_item:
                    new_item = model(**kwargs)
                for key, value in kwargs.items():
                    setattr(new_item, key, value)
            session.add(new_item)
            session.commit()
            session.refresh(new_item)
    return new_item


async def delete_item(model: "Graphemy", item, id="id"):
    id = [getattr(item, i) for i in id]
    engine = Setup.engine[model.__enginename__]
    if Setup.async_engine:
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with async_session() as session:
            item = await session.get(model, id)
            await session.delete(item)
            await session.commit()
    else:
        with Session(engine) as session:
            item = session.get(model, id)
            session.delete(item)
            session.commit()
    return item
