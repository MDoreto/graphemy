import json
from dataclasses import asdict
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.elements import AsBoolean
from sqlmodel import Session, and_, func, or_, select

from graphemy.setup import Setup

from .utils import get_query_filter, get_sort_criteria

if TYPE_CHECKING:
    from graphemy.models import Graphemy


async def get_items(
    model: "Graphemy",
    parameters: list[tuple],
    key_id: str | list[str] = "id",
) -> list[list["Graphemy"] | None]:
    """
    Retrieve items from the database for multiple (filters, keys) parameter sets.

    For each unique combination of (key, filter_string), a single query is constructed
    and executed to optimize database access. The results are grouped back into the
    original structure, ensuring that the final list of lists aligns with the
    provided parameters.

    Args:
        model (Graphemy): The Graphemy (SQLModel) class representing the database table.
        parameters (list[tuple]): A list of tuples where each tuple consists of:
            - A primary key or tuple of primary keys (depending on key_id)
            - A JSON-encoded string representing additional filter criteria
        key_id (str | list[str], optional): The primary key field name(s). Defaults to "id".
            If multiple keys are used, pass a list of field names.

    Returns:
        list[list["Graphemy"] | None]: A nested list of results matching each parameter set.
            Each sublist corresponds to a particular (key, filter) pair.
    """
    # Dictionary to group parameters by their filter string
    groups = {}
    for p in parameters:
        filters = p[1]
        # Build an empty nested structure based on unique filters and key values
        if filters not in groups:
            groups[filters] = {}
        if p[0] not in groups[filters]:
            groups[filters][p[0]] = []

    # For each unique filter string, create and execute a query
    for filter_str, filter_value in groups.items():
        query = select(model)

        # If the primary key is a list, build AND conditions for each field
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
            # Otherwise, use the simple case: the key_id is a single field
            query = query.where(
                getattr(model, key_id).in_(filter_value.keys()),
            )

        # Decode the filter JSON string if provided
        if filter_str:
            query_filter = json.loads(filter_str)
        # Build the actual SQLAlchemy filter conditions
        query_filter = (
            get_query_filter(query_filter, model, []) if filter_str else [True]
        )

        # Execute the query with the given filters
        results = await Setup.execute_query(
            query.where(*query_filter),
            model.__enginename__,
        )

        # Group each result by its corresponding key value
        for r in results:
            key = (
                tuple([getattr(r, i) for i in key_id])
                if isinstance(key_id, list)
                else getattr(r, key_id)
            )
            filter_value[key].append(r)

    # Flatten the nested structure into a single list of lists
    final = []
    [final.extend(value.values()) for value in groups.values()]
    return final


async def get_all(
    model: "Graphemy",
    filters: "Graphemy",
    query_filter: AsBoolean,
    sort: list["Graphemy"] | None,
    offset: int | None,
    limit: int | None,
) -> tuple[list["Graphemy"], int | None]:
    """
    Retrieve all items from the database for a given model, with optional filters, sorting, and pagination.

    Args:
        model (Graphemy): The Graphemy (SQLModel) model class to query.
        filters (Graphemy): An instance of the model (or compatible dataclass) containing
            filtering criteria. This is converted to SQLAlchemy conditions via get_query_filter.
        query_filter (AsBoolean): A SQLAlchemy Boolean expression for additional filtering.
        sort (list["Graphemy"] | None): A list of sort instructions, which are translated
            into ORDER BY clauses via get_sort_criteria.
        offset (int | None): The offset for pagination. Defaults to None.
        limit (int | None): The maximum number of items to return. Defaults to None.

    Returns:
        tuple[list["Graphemy"], int | None]: A tuple containing:
            - A list of fetched rows matching the filters/sorting.
            - The total count of rows (if pagination is used) or None.
    """
    # Base query with the provided "query_filter" conditions
    query = select(model).where(query_filter)

    # If additional filters are provided, convert them to SQLAlchemy conditions
    if filters:
        query = query.where(*get_query_filter(asdict(filters), model, []))

    # Handle offset/limit (pagination); if applied, we also get the total count
    if offset or limit:
        count_query = select(func.count()).select_from(query)
        count = await Setup.execute_query(count_query, model.__enginename__)
        count = count[0]

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
    else:
        count = None

    # Handle sorting instructions
    if sort and len(sort) > 0:
        criteria = get_sort_criteria(sort, model)
        for c in criteria:
            if c[2] == "asc":
                query = query.order_by(getattr(model, c[0]).asc())
            else:
                query = query.order_by(getattr(model, c[0]).desc())

    # Execute the final query
    r = await Setup.execute_query(query, model.__enginename__)

    return r, count


async def put_item(
    model: "Graphemy",
    item: "Graphemy",
    key: list[str],
) -> "Graphemy":
    """
    Insert or update a single item in the database.

    If the primary key does not exist in the database, a new row is inserted.
    Otherwise, the existing row is updated with the provided values.

    Args:
        model (Graphemy): The Graphemy (SQLModel) model class to insert/update.
        item (Graphemy): The item instance containing data to insert or update.
        key (list[str]): A list of field names representing the primary key.

    Returns:
        Graphemy: The inserted or updated model instance.
    """
    # Extract the primary key values from the item
    key = [getattr(item, i) for i in key]

    # Convert the item to a dictionary of field values
    kwargs = vars(item)

    # Retrieve the engine from Setup
    engine = Setup.engine[model.__enginename__]

    # If using async engine, handle insert/update with async session
    if Setup.async_engine:
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with async_session() as session:
            # If no valid primary key, create a new item
            if not key or None in key:
                new_item = model(**kwargs)
            else:
                # Otherwise, try to fetch the existing record and update it
                new_item = await session.get(model, key)
                if not new_item:
                    new_item = model(**kwargs)
                for field_name, value in kwargs.items():
                    setattr(new_item, field_name, value)

            # Add the new or updated item to the session and commit
            session.add(new_item)
            await session.commit()
            await session.refresh(new_item)

    # Otherwise, handle insert/update with a synchronous session
    else:
        with Session(engine) as session:
            if not key or None in key:
                new_item = model(**kwargs)
            else:
                new_item = session.get(model, key)
                if not new_item:
                    new_item = model(**kwargs)
                for field_name, value in kwargs.items():
                    setattr(new_item, field_name, value)

            session.add(new_item)
            session.commit()
            session.refresh(new_item)

    return new_item


async def delete_item(
    model: "Graphemy",
    item: "Graphemy",
    key: list[str],
) -> "Graphemy":
    """
    Delete an item from the database using the provided model and primary key.

    Args:
        model (Graphemy): The Graphemy (SQLModel) model class to delete from.
        item (Graphemy): The instance containing the primary key values to identify the row.
        key (list[str]): The list of field names that form the primary key.

    Returns:
        Graphemy: The deleted item. If no item was found, None is returned (runtime error if not handled).
    """
    # Extract the primary key values
    key = [getattr(item, i) for i in key]

    engine = Setup.engine[model.__enginename__]

    # If using async engine, delete with async session
    if Setup.async_engine:
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with async_session() as session:
            item = await session.get(model, key)
            # If item exists, delete it
            if item:
                await session.delete(item)
                await session.commit()

    # Otherwise, handle deletion with a synchronous session
    else:
        with Session(engine) as session:
            item = session.get(model, key)
            if item:
                session.delete(item)
                session.commit()

    return item
