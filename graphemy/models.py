from datetime import date
from typing import Annotated, Optional,get_args,get_origin

import strawberry
from sqlmodel import SQLModel, literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
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

class DlModel:
    left:str | list[str]
    right:str | list[str]
    def __init__(self, left:str | list[str], right:str | list[str]):
        self.left = left
        self.right = right

def dl_test( left = 'id', right='id'):
    return DlModel(left, right)

class Graphemy(SQLModel):
    _schema = None
    _query = None
    _filter = None
    __customfields__ = {}
    _default_mutation: bool = False
    _delete_mutation: bool = False
    _disable_query: bool = False

    def __init_subclass__(cls, **kwargs):
        to_remove = []
        for attr_name, attr_type in cls.__annotations__.items():
            if hasattr(cls, attr_name):
                attr  = getattr(cls, attr_name)
                if isinstance(attr, DlModel):
                    is_list = get_origin(attr_type) == list
                    if is_list:
                        class_name= get_args(attr_type)
                        class_name = class_name[0]
                    else:
                        class_name = attr_type
                    dl_name=attr.right if isinstance(attr.right, str) else '_'.join(attr.right)
                    dl_name = class_name+ '_' + dl_name

                    print(attr_name,attr_type, is_list, class_name, dl_name)
                    return_type = Annotated[class_name + 'Schema', strawberry.lazy('graphemy.router')]
                    if is_list:
                        return_type = list[return_type]
                    async def new_func(
                        self,
                        info,
                        filters: Annotated[class_name + 'Filter', strawberry.lazy('graphemy.router')]
                        | None = None,
                    ) -> return_type:
                        return await info.context[dl_name].load(
                            [self.bank_id, self.id], {
                                'filters': vars(filters) if filters else None,
                            }
                        )
                    new_func.__name__ = attr_name
                    new_func.dl = class_name
                    new_func.many = is_list
                    new_func.right_field = attr.right
                    new_func.dl_name = dl_name
                    setattr(cls, attr_name,new_func)
                    to_remove.append(attr_name)



        for attr in to_remove:
            del cls.__annotations__[attr_name]


    async def permission_getter(info):
        return True

    @classmethod
    def auth(cls, request_type):
        return Setup.get_auth(cls, request_type)

    @classmethod
    @property
    def filter(cls):
        if cls._filter:
            return cls._filter.default
        return None

    @classmethod
    def query(cls):
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
                strawberry.field(default=None, graphql_type=Optional[field]),
            )
        filter = strawberry.input(name=f'{cls.__name__}Filter')(Filter)
        cls._filter.default = filter

        async def field(
            self, info, filters: filter | None = None
        ) -> list[cls.schema]:
            if not await cls.permission_getter(
                info
            ) or not await Setup.get_permission(cls, info.context, 'query'):
                return []
            data = await get_all(cls, filters, Setup.query_filter(cls, info))
            return data

        return field

    @classmethod
    @property
    def schema(cls):
        return cls._schema

    @classmethod
    def set_schema(cls, classes):
        class Schema:
            pass
        for funcao in [
            func for func in cls.__dict__.values() if hasattr(func,'dl')
        ]:
            print(funcao)
            setattr(
                Schema,
                funcao.__name__,
                strawberry.field(
                    funcao,
                    permission_classes=[
                        Setup.get_auth(
                            classes[funcao.dl if funcao.dl else cls.__name__][
                                0
                            ],
                            'query',
                        )
                    ],
                ),
            )
            if funcao.many:
                async def dataloader(keys: list[tuple]) -> list[cls.schema]:
                    return await get_list(cls, keys, funcao.right_fields)
            else:
                async def dataloader(keys: list[tuple]) -> cls.schema:
                    return await get_one(cls, keys, funcao.right_fields)
        for field, v in cls.__customfields__.items():
            setattr(Schema, field, v)
        cls._schema = strawberry.experimental.pydantic.type(
            cls, all_fields=True, name=f'{cls.__name__}Schema'
        )(Schema)

    @classmethod
    @property
    def mutation(cls):
        from sqlalchemy.inspection import inspect as insp

        pk = [pk.name for pk in insp(cls).primary_key]

        class Filter:
            pass

        for field_name, field in cls.__annotations__.items():
            setattr(
                Filter,
                field_name,
                strawberry.field(default=None, graphql_type=Optional[field]),
            )
        input = strawberry.input(name=f'{cls.__name__}Input')(Filter)

        async def mutation(self, params: input) -> cls.schema:
            return await put_item(cls, params, pk)

        return mutation

    @classmethod
    @property
    def delete_mutation(cls):
        from sqlalchemy.inspection import inspect as insp

        pk = [pk.name for pk in insp(cls).primary_key]

        class Filter:
            pass

        for field_name, field in cls.__annotations__.items():
            if field_name in pk:
                setattr(
                    Filter,
                    field_name,
                    strawberry.field(
                        default=None, graphql_type=Optional[field]
                    ),
                )
        input = strawberry.input(name=f'{cls.__name__}InputPk')(Filter)

        async def mutation(self, params: input) -> cls.schema:
            return await delete_item(cls, params, pk)

        cls._delete = mutation
        return mutation


from datetime import date

from sqlmodel import Session, and_, bindparam, extract, or_, select

engine = Setup.engine


def get_keys(model: 'Graphemy', id: str | list[str]) -> tuple | str:
    """
    Retrieve one or multiple attributes or keys from a Graphemy instance.

    Args:
                    model (Graphemy): An instance of the Graphemy class from which attributes/keys will be retrieved.
                    id (str or list of str): The attribute/key name(s) to be retrieved from the model.

    Returns:
                    str, tuple, or any: The retrieved attribute(s) or key(s) from the model. If 'id' is a single string,the corresponding attribute/key value is returned. If 'id' is a list of strings, a tuple containing the corresponding attribute/key values in the order specified is returned. The returned values may be converted to strings if they are integers or have leading/trailing whitespaces.

    Examples:
                    >>> from graphemy import Graphemy

                    >>> class Hero(Graphemy):
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
    model: 'Graphemy',
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
    model: 'Graphemy',
    parameters: list[tuple],
    id='id',
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
    results = await Setup.execute_query(
        query.where(or_(*query_filters)).params(**params)
    )
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


async def get_one(model: 'Graphemy', parameters: list[tuple], id='id'):
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
    results = await Setup.execute_query(
        query.where(or_(*query_filters)).params(**params)
    )
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


async def get_all(model: 'Graphemy', filters, query_filter):
    query = select(model).where(query_filter)
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
    r = await Setup.execute_query(query)
    return r


async def put_item(model: 'Graphemy', item, id='id', engine=engine):
    id = [getattr(item, i) for i in id]
    kwargs = vars(item)
    engine = Setup.engine
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


async def delete_item(model: 'Graphemy', item, id='id', engine=engine):
    id = [getattr(item, i) for i in id]
    engine = Setup.engine
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
