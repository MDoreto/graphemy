from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, and_, extract, or_, select

from ..schemas.models import DateFilter
from ..setup import Setup
from .utils import get_filter, get_keys

if TYPE_CHECKING:
    from ..models import Graphemy


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
        if not f in filters:
            filters[f] = []
        filters[f].append(p[1][1])
        groups[p] = [] if many else None
        if not p[1][1] in id_groups:
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
                                extract("year", getattr(model, k)) == v[2][1]
                            )
                        if v[0][1]:
                            filter_temp.append(getattr(model, k).in_(list(v[0][1])))
                        if v[1][1] and v[1][1][0]:
                            filter_temp.append(getattr(model, k) >= v[1][1][0])
                        if v[1][1] and v[1][1][1]:
                            filter_temp.append(getattr(model, k) <= v[1][1][1])
                    else:
                        filter_temp.append(getattr(model, k).in_(v))
        else:
            filter_temp = [True]

        query_filters.append(
            and_(*filter_temp, get_filter(model, filters[f], id, params, i))
        )
    results = await Setup.execute_query(
        query.where(or_(*query_filters)).params(**params), model.__enginename__
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
                if not t[0][1] or all([getattr(r, k) in v for k, v in t[0][1] if v]):
                    if many:
                        groups[t].append(r)
                    else:
                        groups[t] = r
    return groups.values()


async def get_all(model: "Graphemy", filters, query_filter) -> list:
    query = select(model).where(query_filter)
    if filters:
        filters = vars(filters)
        for k, v in filters.items():
            if isinstance(v, DateFilter):
                if v.year:
                    query = query.where(extract("year", getattr(model, k)) == v.year)
                if v.items:
                    query = query.where(getattr(model, k).in_(v.items))
                if v.range and v.range[0]:
                    query = query.where(getattr(model, k) >= (v.range[0]))
                if v.range and v.range[1]:
                    query = query.where(getattr(model, k) <= (v.range[1]))
            elif filters[k]:
                query = query.where(getattr(model, k).in_(filters[k]))
    r = await Setup.execute_query(query, model.__enginename__)
    return r


async def put_item(model: "Graphemy", item, id="id"):
    id = [getattr(item, i) for i in id]
    kwargs = vars(item)
    engine = Setup.engine[model.__enginename__]
    if Setup.async_engine:
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
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
            engine, class_=AsyncSession, expire_on_commit=False
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
