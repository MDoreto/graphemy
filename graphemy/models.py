import re
from sqlmodel import SQLModel
from strawberry.types.base import StrawberryType

from .dl import Dl
from .schemas.generators import get_dl_function
from .setup import Setup


class Graphemy(SQLModel):
    """
    Base class for Graphemy entities, providing automatic table naming,
    dynamic DataLoader integration, and class registration within `Setup`.

    Inherits from:
        SQLModel: The SQLModel base class for defining database models.

    Attributes:
        __strawberry_schema__ (StrawberryType): Holds a Strawberry GraphQL type
            associated with this model.
        __enable_put_mutation__ (bool | None): Flag indicating whether PUT (update)
            mutations are enabled for this model. If None, will fallback to a
            global default in Setup.
        __enable_delete_mutation__ (bool | None): Flag indicating whether DELETE
            mutations are enabled for this model. If None, will fallback to a
            global default in Setup.
        __enable_query__ (bool | None): Flag indicating whether queries for this
            model are enabled. If None, will fallback to a global default in Setup.
        __queryname__ (str): The name used in the generated GraphQL query field
            (e.g., "users" for a "User" model). Defaults to the table name + "s".
        __enginename__ (str): The name of the configured engine from Setup's
            engine dict to use for database operations. Defaults to "default".
    """

    __strawberry_schema__: StrawberryType = None
    __enable_put_mutation__: bool | None = None
    __enable_delete_mutation__: bool | None = None
    __enable_query__: bool | None = None
    __queryname__: str = ""
    __enginename__: str = "default"

    class Strawberry:
        """
        A nested class used to hold Strawberry-specific metadata if needed.
        Intended for extension or configuration by subclasses.
        """

    def __init_subclass__(cls) -> None:
        """
        Hook that is called when a subclass of Graphemy is defined.

        - Automatically sets the table name (e.g., `UserProfile` -> `user_profile`).
        - Registers the class in `Setup.classes`.
        - Converts any attributes defined as a Dl instance into a GraphQL-compatible
          field using `get_dl_function`.
        - Removes these Dl attributes from the class annotations to prevent
          SQLModel from interpreting them as standard columns.
        """

        # Auto-generate a table name by inserting underscores before capital letters
        # (e.g., UserProfile -> user_profile)
        cls.__tablename__ = re.sub(
            r"(?<!^)(?=[A-Z])",
            "_",
            cls.__name__,
        ).lower()

        # If __queryname__ is not explicitly set, use the table name + 's'
        cls.__queryname__ = (
            cls.__queryname__ if cls.__queryname__ else cls.__tablename__ + "s"
        )

        # Register this class in the Setup so it can be used for auto schema generation
        Setup.classes[cls.__name__] = cls

        # Prepare a list for attributes that are Dl instances,
        # so we can convert them into GraphQL DataLoader functions.
        to_remove = []

        # Loop through annotated attributes
        for attr_name, attr_type in cls.__annotations__.items():
            if hasattr(cls, attr_name):
                attr_value = getattr(cls, attr_name)
                # If the attribute is a Dl instance, convert it to a GraphQL field
                if isinstance(attr_value, Dl):
                    to_remove.append(attr_name)
                    dl_field = get_dl_function(
                        attr_name,
                        attr_type,
                        attr_value,
                    )
                    # Replace the Dl instance with the generated GraphQL field
                    setattr(cls, attr_name, dl_field)

        # Remove the Dl attributes from the annotations to avoid issues with SQLModel
        for attr in to_remove:
            del cls.__annotations__[attr]

    async def permission_getter(self: dict, request_type: str) -> bool:
        """
        Placeholder async method for checking permissions at the model level.

        Override this method in subclasses to provide custom logic that
        determines whether certain operations (e.g., read, create, update, delete)
        are allowed based on context, user roles, etc.

        Args:
            request_type (str): The type of GraphQL request (e.g., 'query', 'mutation').

        Returns:
            bool: True if the request is allowed, False otherwise.
        """
        pass
