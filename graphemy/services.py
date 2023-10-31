from datetime import date
from typing import TYPE_CHECKING

from sqlmodel import Session, and_, bindparam, extract, or_, select

from .setup import engine

if TYPE_CHECKING:
    from .models import MyDate, MyModel


def get_keys(model: 'MyModel', id: str | list[str]) -> tuple | str:
    if isinstance(id, list):
        return tuple([getattr(model, id[i]) for i in range(len(id))])
    value = getattr(model, id)
    if isinstance(value, int):
        value = str(value)
    if isinstance(value, str):
        value = value.strip()
    return value


def get_filter(
    model: 'MyModel',
    keys,
    id,
    params: dict,
    i: int,
    contains: bool = False,
    contains_fore: bool = False,
):
    if isinstance(id, list):
        filter = []
        for j, key in enumerate(keys):
            f = []
            if None not in key:
                for k in range(len(id)):
                    f.append(
                        getattr(model, id[k])
                        == bindparam(
                            f'p{i}_{j}_{k}',
                            literal_execute=not isinstance(key[k], date),
                        )
                    )
                    params[f'p{i}_{j}_{k}'] = key[k]
                filter.append(and_(*f))
            else:
                filter.append(False)
        return or_(*filter)
    elif None in keys:
        keys.remove(None)
    params[f'p{i}'] = keys
    if contains:
        return or_(*[getattr(model, id).contains(valor) for valor in keys])
    if contains_fore:
        return or_(
            *[
                getattr(model, id).in_(
                    [a.strip() for a in ','.join(keys).split(',')]
                )
            ]
        )
    return getattr(model, id).in_(
        bindparam(f'p{i}', expanding=True, literal_execute=True)
    )


async def get_list(
    model: 'MyModel',
    parameters: list[tuple],
    id='id',
    engine=engine,
    contains=False,
    contains_fore=False,
):
    groups = {}
    id_groups = {}
    filters = {}
    params = {}
    for p in parameters:
        f = tuple([p[0], p[2]])
        if not f in filters:
            filters[f] = []
        filters[f].append(p[1][1])
        groups[p] = []
        if not p[1][1] in id_groups:
            id_groups[p[1][1]] = []
        id_groups[p[1][1]].append(p)
    query = select(model)
    query_filters = []
    for i, f in enumerate(filters):
        if f[0][1]:
            filter_temp = []
            for k, v in f[0][1]:
                if v:
                    if isinstance(v, tuple):
                        if v[2][1]:
                            filter_temp.append(
                                extract('year', getattr(model, k)) == v[2][1]
                            )
                        if v[0][1]:
                            filter_temp.append(
                                getattr(model, k).in_(list(v[0][1]))
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
            and_(
                *filter_temp,
                get_filter(
                    model,
                    filters[f],
                    id,
                    params,
                    i,
                    contains=contains,
                    contains_fore=contains_fore,
                ),
            )
        )
    with Session(engine) as session:
        results = session.exec(
            query.where(or_(*query_filters)).params(**params)
        ).all()
        for r in results:
            if contains:
                for it in get_keys(r, id).split(','):
                    it = it.strip()
                    if it in id_groups:
                        for t in id_groups[it]:
                            if not t[0][1] or all(
                                [getattr(r, k) in v for k, v in t[0][1] if v]
                            ):
                                groups[t].append(r)
            elif contains_fore:
                temp = get_keys(r, id)
                for key, v in id_groups.items():
                    if temp in key:
                        for t in v:
                            groups[t].append(r)

            else:
                temp = id_groups[get_keys(r, id)]
                if len(temp) == 1:
                    key = temp[0]
                    groups[key].append(r)
                else:
                    for t in temp:
                        if not t[0][1] or all(
                            [getattr(r, k) in v for k, v in t[0][1] if v]
                        ):
                            groups[key].append(r)
    return groups.values()


async def get_one(
    model: 'MyModel', parameters: list[tuple], id='id', engine=engine
):
    groups = {}
    id_groups = {}
    filters = {}
    params = {}
    for p in parameters:
        f = tuple([p[0], p[2]])
        if not f in filters:
            filters[f] = []
        filters[f].append(p[1][1])
        groups[p] = None
        if not p[1][1] in id_groups:
            id_groups[p[1][1]] = []

        id_groups[p[1][1]].append(p)
    query = select(model)
    query_filters = []
    for i, f in enumerate(filters):
        if f[0][1]:
            filter_temp = []
            for k, v in f[0][1]:
                if v:
                    if isinstance(v[0], tuple):
                        print(v)
                        if v[2][1]:
                            filter_temp.append(
                                extract('year', getattr(model, k)) == v[2][1]
                            )
                        if v[0][1]:
                            filter_temp.append(
                                getattr(model, k).in_(list(v[0][1]))
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
            and_(*filter_temp, get_filter(model, filters[f], id, params, i))
        )
    with Session(engine) as session:
        results = session.exec(
            query.where(or_(*query_filters)).params(**params)
        ).all()
        for r in results:
            temp = id_groups[get_keys(r, id)]
            if len(temp) == 1:
                key = temp[0]
                groups[key] = r
            else:
                for t in temp:
                    if not t[0][1] or all(
                        [getattr(r, k) in v for k, v in t[0][1] if v]
                    ):
                        groups[key] = r
    return groups.values()


async def get_all(model: 'MyModel', filters, engine=engine):
    query = select(model)
    if filters:
        filters = vars(filters)
        for k, v in filters.items():
            if isinstance(v, MyDate):
                if v.year:
                    query = query.where(
                        extract('year', getattr(model, k)) == v.year
                    )
                if v.items:
                    query = query.where(getattr(model, k).in_(v.items))
                if v.range and v.range[0]:
                    query = query.where(getattr(model, k) >= (v.range[0]))
                if v.range and v.range[1]:
                    query = query.where(getattr(model, k) <= (v.range[1]))
            elif filters[k]:
                query = query.where(getattr(model, k).in_(filters[k]))
    with Session(engine) as session:
        r = session.exec(query).all()
    return r


async def put_item(model: 'MyModel', item, id='id', engine=engine):
    id = [getattr(item, i) for i in id]
    kwargs = vars(item)
    with Session(engine) as session:
        if not id:
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


async def delete_item(model: 'MyModel', item, id='id', engine=engine):
    id = [getattr(item, i) for i in id]
    with Session(engine) as session:
        item = session.get(model, id)
        session.delete(item)
        session.commit()
    return item
