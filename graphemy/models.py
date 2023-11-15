import inspect
import os
from datetime import date
from typing import Annotated, Optional

import strawberry
from sqlmodel import SQLModel, literal

from .setup import Setup


def set_dl(func):
    if not func.dl:
        return func
    f = func.dl + 'Filter'
    s = func.dl + 'Schema'
    if not func.many:

        async def new_func(
            self,
            info,
            filters: Annotated[f, strawberry.lazy('graphemy.router')]
            | None = None,
        ) -> Annotated[s, strawberry.lazy('graphemy.router')] | None:
            return await func(
                self,
                info,
                {
                    'filters': vars(filters) if filters else None,
                    'list_filters': None,
                },
            )

    else:

        async def new_func(
            self,
            info,
            filters: Annotated[f, strawberry.lazy('graphemy.router')]
            | None = None,
            list_filters: ListFilters | None = None,
        ) -> list[Annotated[s, strawberry.lazy('graphemy.router')]]:
            return await func(
                self,
                info,
                {
                    'filters': vars(filters) if filters else None,
                    'list_filters': vars(list_filters)
                    if list_filters
                    else None,
                },
            )

    new_func.__name__ = func.__name__
    return new_func


@strawberry.input
class ListFilters:
    field: str
    asc: bool


@strawberry.input
class MyDate:
    range: list[date] | None = None
    items: list[date] | None = None
    year: int | None = None


class MyModel(SQLModel):
    _schema = None
    _filter = None
    _query = None
    _mutation = None
    _delete = None
    _input = None
    _default_mutation = False
    __customfields__ = {}
    _default_mutation = False
    _delete_mutation = False

    @classmethod
    @property
    def auth(cls):
        folder = os.path.relpath(inspect.getfile(cls))
        return Setup.get_auth(folder)

    @classmethod
    @property
    def filter(cls):
        if not cls._filter:

            class Filter:
                pass

            for field_name, field in cls.__annotations__.items():
                field = (
                    MyDate
                    if (field == date or field == (date | None))
                    else list[field]
                )
                setattr(
                    Filter,
                    field_name,
                    strawberry.field(
                        default=None, graphql_type=Optional[field]
                    ),
                )
            cls._filter = strawberry.input(name=f'{cls.__name__}Filter')(
                Filter
            )
        return cls._filter

    @classmethod
    @property
    def query(cls):
        if not cls._query:
            folder = os.path.relpath(inspect.getfile(cls))

            async def field(
                self, info, filters: cls.filter | None = None
            ) -> list[cls.schema]:
                if not Setup.get_permission(folder, info):
                    return []
                return await get_all(cls, filters)

            cls._query = field
        return cls._query

    @classmethod
    @property
    def schema(cls):
        return cls._schema

    @classmethod
    def set_schema(cls, classes):
        if not cls._schema:

            class Schema:
                pass

            for funcao in [
                func for func in cls.__dict__.values() if hasattr(func, 'dl')
            ]:
                setattr(
                    Schema,
                    funcao.__name__,
                    strawberry.field(
                        set_dl(funcao),
                        permission_classes=[
                            Setup.get_auth(
                                classes[
                                    funcao.dl if funcao.dl else cls.__name__
                                ][1]
                            )
                        ],
                    ),
                )
        cls._schema = strawberry.experimental.pydantic.type(
            cls, all_fields=True, name=f'{cls.__name__}Schema'
        )(Schema)

    @classmethod
    @property
    def input(cls):
        if not cls._input:

            class Filter:
                pass

            for field_name, field in cls.__annotations__.items():
                setattr(
                    Filter,
                    field_name,
                    strawberry.field(
                        default=None, graphql_type=Optional[field]
                    ),
                )
            cls._input = strawberry.input(name=f'{cls.__name__}Input')(Filter)
        return cls._input

    @classmethod
    @property
    def mutation(cls):
        from sqlalchemy.inspection import inspect as insp

        pk = [pk.name for pk in insp(cls).primary_key]
        if not cls._mutation:

            async def mutation(self, params: cls.input) -> cls.schema:
                return await put_item(cls, params, pk)

            cls._mutation = mutation
        return cls._mutation

    @classmethod
    @property
    def delete_mutation(cls):
        from sqlalchemy.inspection import inspect as insp

        pk = [pk.name for pk in insp(cls).primary_key]
        if not cls._delete:

            async def mutation(self, params: cls.input) -> cls.schema:
                return await delete_item(cls, params, pk)

            cls._delete = mutation
        return cls._delete


from datetime import date

from sqlmodel import Session, and_, bindparam, extract, or_, select

engine = Setup.engine


def get_keys(model: 'MyModel', id: str | list[str]) -> tuple | str:
    """
    Retrieve one or multiple attributes or keys from a MyModel instance.

    Args:
        model (MyModel): An instance of the MyModel class from which attributes/keys will be retrieved.
        id (str or list of str): The attribute/key name(s) to be retrieved from the model.

    Returns:
        str, tuple, or any: The retrieved attribute(s) or key(s) from the model. If 'id' is a single string,the corresponding attribute/key value is returned. If 'id' is a list of strings, a tuple containing the corresponding attribute/key values in the order specified is returned. The returned values may be converted to strings if they are integers or have leading/trailing whitespaces.

    Examples:
        >>> from graphemy import MyModel

        >>> class Hero(MyModel):
        ...     name:str
        ...     power_level:int

        >>> hero_instance = Hero(name='Superman', power_level=100)

        >>> get_keys(hero_instance, 'name')
        'Superman'
        >>> get_keys(hero_instance, 'power_level')
        100
        >>> get_keys(hero_instance, ['name', 'power_level'])
        ('Superman', 100)
    """
    if isinstance(id, list):
        return tuple([getattr(model, id[i]) for i in range(len(id))])
    value = getattr(model, id)
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
                literal(value).like('%' + getattr(model, id) + '%')
                for value in keys
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
                    if isinstance(v[0], tuple):
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
    engine = Setup.engine
    with Session(engine) as session:
        results = session.exec(
            query.where(or_(*query_filters)).params(**params)
        ).all()
        for r in results:
            if contains:
                key = get_keys(r, id)
                for i in id_groups:
                    if i in key:
                        for t in id_groups[i]:
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
                            groups[t].append(r)
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
    engine = Setup.engine
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
                        groups[t] = r
    return groups.values()


async def get_all(model: 'MyModel', filters, engine=None):
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
    engine = Setup.engine
    with Session(engine) as session:
        r = session.exec(query).all()
    return r


async def put_item(model: 'MyModel', item, id='id', engine=engine):
    id = [getattr(item, i) for i in id]
    kwargs = vars(item)
    engine = Setup.engine
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


async def delete_item(model: 'MyModel', item, id='id', engine=engine):
    id = [getattr(item, i) for i in id]
    engine = Setup.engine
    with Session(engine) as session:
        item = session.get(model, id)
        session.delete(item)
        session.commit()
    return item
