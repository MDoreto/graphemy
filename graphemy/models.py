from sqlmodel import SQLModel
from strawberry.type import StrawberryType
from strawberry.types import Info

from .dl import Dl
from .schemas.generators import get_dl_function
from .setup import Setup


class Graphemy(SQLModel):
    __strawberry_schema__: StrawberryType = None
    __enable_put_mutation__: bool | None = None
    __enable_delete_mutation__: bool | None = None
    __enable_query__: bool | None = None
    __queryname__: str = ''
    __enginename__: str = 'default'

    class Strawberry:
        pass

    def __init_subclass__(cls):
        cls.__queryname__ = (
            cls.__queryname__ if cls.__queryname__ else cls.__tablename__ + 's'
        )
        Setup.classes[cls.__name__] = cls
        to_remove = []
        for attr_name, attr_type in cls.__annotations__.items():
            if hasattr(cls, attr_name):
                attr_value = getattr(cls, attr_name)
                if isinstance(attr_value, Dl):
                    to_remove.append(attr_name)
                    dl_field = get_dl_function(
                        attr_name, attr_type, attr_value
                    )
                    setattr(cls, attr_name, dl_field)
        for attr in to_remove:
            del cls.__annotations__[attr]

    async def permission_getter(info: Info) -> bool:
        return True
