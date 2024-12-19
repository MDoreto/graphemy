import json
from dataclasses import asdict
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.elements import AsBoolean
from sqlmodel import Session, and_, func, or_, select

from graphemy.setup import Setup

from .utils import get_query_filter, multiple_sort

if TYPE_CHECKING:
    from graphemy.models import Graphemy

async def get_items(
    model: "Graphemy",
    parameters: list[tuple],
    key_id: str | list[str] = "id",
) -> list[list["Graphemy"] | None]:
    groups = {}
    for p in parameters:
        filters = p[1]
        if filters not in groups:
            groups[filters] = {}
        if p[0] not in groups[filters]:
            groups[filters][p[0]] = []
    for filter_str, filter_value in groups.items():
        query = select(model)
        if isinstance(key_id, list):
            conditions = [
                and_(
                    *[
                        getattr(model, column) == key[i]
                        for i, column in enumerate(key_id)
                    ],
                )
                for key in filter_value
            ]
            query = query.where(or_(*conditions))
        else:
            query = query.where(getattr(model, key_id).in_(filter_value.values()))
        if filter_str:
            query_filter = json.loads(filter_str)
        query_filter = (
            get_query_filter(filter, query_filter, []) if filter_str else [True]
        )
        results = await Setup.execute_query(
            select(model).where(*query_filter),
            model.__enginename__,
        )
        for r in results:
            key = (
                tuple([getattr(r, i) for i in key_id])
                if isinstance(key_id, list)
                else getattr(r, key_id)
            )
            filter_value[key].append(r)
    final = []
    [final.extend(value.values()) for value in groups.values()]
    return final


async def get_all(
    model: "Graphemy",
    filters: "Graphemy",
    query_filter:AsBoolean,
    sort: list["Graphemy"] | None,
    offset: int | None,
    limit: int | None,
) -> tuple[list["Graphemy"], int | None]:
    query = select(model).where(query_filter)
    if filters:
        query = query.where(*get_query_filter(asdict(filters), model, []))
    if offset or limit:
        count = await Setup.execute_query(select(func.count()).select_from(query), model.__enginename__)
        count = count[0]
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
    else:
        count = None
    r = await Setup.execute_query(query, model.__enginename__)
    if sort and len(sort) > 0:
        r = multiple_sort(model, r, sort)
    return r, count


async def put_item(model: "Graphemy", item:"Graphemy", key:list[str]) -> "Graphemy":
    key = [getattr(item, i) for i in key]
    kwargs = vars(item)
    engine = Setup.engine[model.__enginename__]
    if Setup.async_engine:
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with async_session() as session:
            if not key or None in key:
                new_item = model(**kwargs)
            else:
                new_item = await session.get(model, key)
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


async def delete_item(model: "Graphemy", item:"Graphemy", key:list[str]) -> "Graphemy":
    key = [getattr(item, i) for i in key]
    engine = Setup.engine[model.__enginename__]
    if Setup.async_engine:
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with async_session() as session:
            item = await session.get(model, key)
            await session.delete(item)
            await session.commit()
    else:
        with Session(engine) as session:
            item = session.get(model, key)
            session.delete(item)
            session.commit()
    return item
