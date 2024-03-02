from strawberry.types import Info
from sqlmodel import  SQLModel
from .setup import Setup
from .schemas.generators import  get_dl_function
from .dl import DlModel
from strawberry.type import StrawberryType

class Graphemy(SQLModel):
    __strawberry_schema__:StrawberryType = None
    __put_mutation__: bool = False
    __delete_mutation__: bool = False
    __disable_query__: bool = False
    __query__:str = ''
    class Strawberry:
        pass

    def __init_subclass__(cls):
        cls.__query__ = cls.__query__ if cls.__query__ else cls.__tablename__ +'s'
        Setup.classes[cls.__name__] = cls
        to_remove = []
        for attr_name, attr_type in cls.__annotations__.items():
            if hasattr(cls, attr_name):
                attr_value = getattr(cls, attr_name)
                if isinstance(attr_value, DlModel):
                    to_remove.append(attr_name)
                    dl_field = get_dl_function(attr_name, attr_type, attr_value)
                    setattr(cls, attr_name, dl_field)
        for attr in to_remove:
            del cls.__annotations__[attr]

    async def permission_getter(info:Info) -> bool:
        return True