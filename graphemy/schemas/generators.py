import strawberry
from typing import Annotated, get_args, get_origin
from ..dl import DlModel
from typing import TypeVar
from strawberry.types import Info
from ..setup import Setup
from typing import TYPE_CHECKING
from ..database.operations import get_items, get_all, put_item, delete_item
from strawberry.tools import merge_types

if TYPE_CHECKING:
    from ..models import Graphemy

T = TypeVar('T')

def set_schema(cls:"Graphemy", functions:dict):
    class Schema:
        pass

    for funcao in [
        func for func in cls.__dict__.values() if hasattr(func, 'dl')
    ]:
        returned_class:"Graphemy" = Setup.classes[funcao.dl]
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
            returned_schema = returned_class.schema
            if funcao.many:
                returned_schema = list[returned_schema]

            async def dataloader(
                keys: list[tuple],
            ) -> returned_schema:
                return await get_items(
                    returned_class, keys, funcao.target, funcao.many
                )

            dataloader.__name__ = funcao.dl_name
            functions[funcao.dl_name] = (dataloader, returned_class)
    sch = strawberry.experimental.pydantic.type(
        cls, all_fields=True, name=f'{cls.__name__}Schema1'
    )(Schema)
    temp = strawberry.type(cls.Strawberry, name=f'{cls.__name__}Schema2')
    if temp.__annotations__:
        sch = merge_types(f'{cls.__name__}Schema1', (sch, temp))
    cls.schema = sch

def get_dl_function(
    field_name: str,
    field_type: T,
    field_value: DlModel,
) -> callable:
    """Generates a DataLoader function dynamically based on the field's specifications."""

    # Determine if the field_type is a list and extract the inner type
    is_list = get_origin(field_type) == list
    class_type = get_args(field_type)[0] if is_list else field_type

    # Formulate DataLoader name with consideration for lazy-loaded types
    dl_name = 'dl_' + class_type + '_' + (
        field_value.target if isinstance(field_value.target, str) else '_'.join(field_value.target)
    )

    # Define the return type using Strawberry's lazy type resolution
    return_type = Annotated[
        f'{class_type}Schema',
        strawberry.lazy('graphemy.router'),
    ]
    if is_list:
        return_type = list[return_type]

    async def loader_func(
        self,
        info: Info,
        filters: Annotated[
            f'{class_type}Filter',
            strawberry.lazy('graphemy.router'),
        ] = None,
    ) -> return_type:
        """The dynamically generated DataLoader function."""
        filter_args = vars(filters) if filters else None
        source_value = (
            [getattr(self, attr) for attr in field_value.source]
            if isinstance(field_value.source, list)
            else getattr(self, field_value.source)
        )
        return await info.context[dl_name].load(source_value, {'filters': filter_args})

    # Customize the function attributes for introspection or other purposes
    loader_func.__name__ = field_name
    loader_func.dl = class_type
    loader_func.many = is_list
    loader_func.target = field_value.target
    loader_func.dl_name = dl_name

    return loader_func

