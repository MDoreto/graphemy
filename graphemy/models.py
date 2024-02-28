from datetime import date
from typing import Annotated, Optional, get_args, get_origin

import strawberry
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from strawberry.field import StrawberryField
from .setup import Setup


@strawberry.input
class DateFilter:
    range: list[date] | None = None
    items: list[date] | None = None
    year: int | None = None


class DlModel:
    left: str | list[str]
    right: str | list[str]

    def __init__(self, left: str | list[str], right: str | list[str]):
        self.left = left
        self.right = right


def Dl(left='id', right='id'):
    return DlModel(left, right)


class Graphemy(SQLModel):
    _schema = None
    _query = None
    _filter = None
    __customfields__ = {}
    _default_mutation: bool = False
    _delete_mutation: bool = False
    _disable_query: bool = False

    class Strawberry:
        pass

    def __init_subclass__(cls, **kwargs):
        to_remove = []
        for attr_name, attr_type in cls.__annotations__.items():
            if hasattr(cls, attr_name):
                attr_value = getattr(cls, attr_name)
                if isinstance(attr_value, DlModel):
                    print(attr_name,attr_type, type(attr_value))  
                    is_list = get_origin(attr_type) == list
                    if is_list:
                        class_name = get_args(attr_type)
                        class_name = class_name[0]
                    else:
                        class_name = attr_type
                    dl_name = (
                        attr_value.right
                        if isinstance(attr_value.right, str)
                        else '_'.join(attr_value.right)
                    )
                    dl_name = 'dl_' + class_name + '_' + dl_name
                    return_type = Annotated[
                        class_name + 'Schema',
                        strawberry.lazy('graphemy.router'),
                    ]
                    if is_list:
                        return_type = list[return_type]

                    async def new_func(
                        self,
                        info,
                        filters: Annotated[
                            class_name + 'Filter',
                            strawberry.lazy('graphemy.router'),
                        ]
                        | None = None,
                    ) -> return_type:
                        return await info.context[dl_name].load(
                            [getattr(self, at) for at in attr_value.left]
                            if isinstance(attr_value.left, list)
                            else getattr(self, attr_value.left),
                            {
                                'filters': vars(filters) if filters else None,
                            },
                        )

                    new_func.__name__ = attr_name
                    new_func.dl = class_name
                    new_func.many = is_list
                    new_func.right_fields = attr_value.right
                    new_func.dl_name = dl_name
                    setattr(cls, attr_name, new_func)
                    to_remove.append(attr_name)

        for attr in to_remove:
            del cls.__annotations__[attr]

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
                DateFilter
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
    def set_schema(cls, classes, functions):
        class Schema:
            pass

        for funcao in [
            func for func in cls.__dict__.values() if hasattr(func, 'dl')
        ]:
            returned_class = classes[funcao.dl][
                0
            ]
            setattr(
                Schema,
                funcao.__name__,
                strawberry.field(
                    funcao,
                    permission_classes=[
                        Setup.get_auth(
                            returned_class,
                            'query',
                        )
                    ],
                ),
            )
            if not funcao.dl_name in functions:
                if funcao.many:

                    async def dataloader(
                        keys: list[tuple],
                    ) -> list[returned_class.schema]:
                        return await get_items(
                            returned_class, keys, funcao.right_fields, True
                        )

                else:

                    async def dataloader(
                        keys: list[tuple],
                    ) -> returned_class.schema:
                        return await get_items(
                            returned_class, keys, funcao.right_fields, False
                        )

                dataloader.__name__ = funcao.dl_name
                functions[funcao.dl_name] = (dataloader, returned_class)
        for name, typying in cls.Strawberry.__annotations__.items():
            print(name)
            cls.__annotations__[name] = typying
            setattr(Schema, name, getattr(cls.Strawberry, name))
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
    return getattr(model, id).in_(
        bindparam(f'p{i}', expanding=True, literal_execute=True)
    )


async def get_items(
    model: 'Graphemy', parameters: list[tuple], id='id', many=True
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
            if many:
                groups[key].append(r)
            else:
                groups[key] = r
        else:
            for t in temp:
                if not t[0][1] or all(
                    [getattr(r, k) in v for k, v in t[0][1] if v]
                ):
                    if many:
                        groups[key].append(r)
                    else:
                        groups[key] = r
    return groups.values()


async def get_all(model: 'Graphemy', filters, query_filter):
    query = select(model).where(query_filter)
    if filters:
        filters = vars(filters)
        for k, v in filters.items():
            if isinstance(v, DateFilter):
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
