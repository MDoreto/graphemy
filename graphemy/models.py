import re

from sqlmodel import SQLModel
from strawberry.types.base import StrawberryType

from .dl import Dl
from .schemas.generators import get_dl_function
from .setup import Setup


class Graphemy(SQLModel):
    """An extension of SQLModel that integrates Strawberry GraphQL functionalities,
    enabling the dynamic generation of GraphQL schemas directly from SQLModel definitions.
    This class supports configuring GraphQL operations such as queries and mutations,
    and facilitates the management of permissions for these operations.

    Attributes:
        __strawberry_schema__ (StrawberryType): Holds the GraphQL schema associated with
            this model, allowing for integration with the Strawberry GraphQL library.
        __enable_put_mutation__ (bool | None): Controls whether PUT mutations (update
            operations) are enabled for this model in the GraphQL API. Set to `True` to
            enable, `False` to disable, or `None` to use default settings.
        __enable_delete_mutation__ (bool | None): Determines whether DELETE mutations
            (delete operations) are enabled for this model in the GraphQL API. Set to
            `True` to enable, `False` to disable, or `None` to use default settings.
        __enable_query__ (bool | None): Specifies whether the model can be queried via
            the GraphQL API. Set to `True` to enable queries, `False` to disable, or
            `None` to leave it unset.
        __queryname__ (str): Provides a custom name for GraphQL queries related to this
            model. Defaults to the model's table name plus 's' (e.g., 'users' for a User
            model) if not explicitly set.
        __enginename__ (str): Identifier for the database engine used by this model,
            useful for applications that connect to multiple databases or require
            specific database configurations.
    Classes:
        Graphemy: An extended SQLModel that incorporates GraphQL functionalities by using
        Strawberry GraphQL. This class allows defining GraphQL schemas, query names,
        engine names, and supports dynamic field resolution using dependency injection.

        Strawberry: An inner class used to encapsulate GraphQL-specific configurations
        and properties for the Graphemy class.

    Methods:
        __init_subclass__: Automatically called when a subclass of Graphemy is defined.
            Sets up the necessary GraphQL configurations and registers the subclass in a
            setup registry for further reference.
        permission_getter: Async static method intended to be overridden to provide
            custom logic for determining user permissions for executing GraphQL queries.
            Should return `True` if the query is permitted, `False` otherwise.

    """

    __strawberry_schema__: StrawberryType = None
    __enable_put_mutation__: bool | None = None
    __enable_delete_mutation__: bool | None = None
    __enable_query__: bool | None = None
    __queryname__: str = ""
    __enginename__: str = "default"

    class Strawberry:
        pass

    def __init_subclass__(cls):
        cls.__tablename__ = re.sub(
            r"(?<!^)(?=[A-Z])",
            "_",
            cls.__name__,
        ).lower()
        cls.__queryname__ = (
            cls.__queryname__ if cls.__queryname__ else cls.__tablename__ + "s"
        )
        Setup.classes[cls.__name__] = cls
        to_remove = []
        for attr_name, attr_type in cls.__annotations__.items():
            if hasattr(cls, attr_name):
                attr_value = getattr(cls, attr_name)
                if isinstance(attr_value, Dl):
                    to_remove.append(attr_name)
                    dl_field = get_dl_function(
                        attr_name,
                        attr_type,
                        attr_value,
                    )
                    setattr(cls, attr_name, dl_field)
        for attr in to_remove:
            del cls.__annotations__[attr]

    async def permission_getter(self: dict, request_type: str) -> bool:
        pass
