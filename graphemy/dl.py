from collections.abc import Callable
from dataclasses import asdict
from typing import TYPE_CHECKING, Annotated, TypeVar

from strawberry.dataloader import DataLoader
from strawberry.types.base import StrawberryType

if TYPE_CHECKING:
    from .models import Graphemy
import json


class Dl:
    """A utility class designed to facilitate the linking of source and target fields
    across different models. This is particularly useful for setting up data loaders
    where fields from one model may depend on fields in another, and if foreign keys should be created based on relationships.

    Attributes:
        source (str | list[str]): The source field(s) from where data is to be fetched.
        target (str | list[str]): The target field(s) where data is to be deposited.
        foreign_key (bool): Indicates whether the relationship should create a foreign key
            (default is False).

    Raises:
        ValueError: If the types of source and target do not match, or if they are lists
            and do not have the same length.

    """

    source: str | list[str]
    target: str | list[str]
    foreign_key: bool | None = None

    def __init__(
        self,
        source: str | list[str],
        target: str | list[str],
        foreign_key: bool | None = None,
    ) -> None:
        if type(source) is not type(target):
            msg = "Source and target must have the same length."
            raise ValueError(msg)
        if type(source) is list:
            if len(source) != len(target):
                msg = "Source and target must have the same length."
                raise ValueError(
                    msg,
                )
            ids = {}
            for i, key in enumerate(target):
                ids[key] = source[i]
            target.sort()
            source = [ids[key] for key in target]
        self.source = source
        self.target = target
        self.foreign_key = foreign_key


ReturnType: TypeVar = list["Graphemy"] | Annotated["Graphemy", ".models"] | None



class GraphemyDataLoader(DataLoader):
    """A specialized DataLoader for loading Graphemy objects with optional filtering.
    The loader expects keys along with optional filtering and ordering arguments.
    """

    def __init__(
        self,
        filter_method: Callable[[ReturnType, dict | None], ReturnType]
        | None = None,
        context: dict | None = None,
        **kwargs:dict,
    ) -> None:
        """Initialize the GraphemyDataLoader.

        Parameters
        ----------
        filter_method : Callable[[ReturnType, dict | None], ReturnType] | None
            An optional callable to further filter or modify the data after it is loaded.
            It receives the loaded data and the context as arguments.
        context : dict | None
            Optional context information to be passed to the filter method.
        kwargs : dict
            Additional arguments passed to the parent DataLoader.

        """
        self.filter_method = filter_method
        self.context = context
        super().__init__(**kwargs)

    async def load(
        self,
        keys:list,
        where: StrawberryType | None = None,
        order_by: StrawberryType | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> ReturnType:
        """Load data given keys, an optional 'where' filter, and optional 'order_by' instructions.

        Parameters
        ----------
        keys : str | list[str] | tuple[str, ...]
            The identifying keys for which data should be loaded.
        where : object | None
            A Strawberry input type instance representing filtering conditions.
        order_by : object | None
            A Strawberry input type instance representing ordering instructions.

        Returns
        -------
        ReturnType
            The loaded data, potentially filtered by the filter_method if provided.

        """
        if isinstance(keys, list):
            normalized_keys = tuple(keys)
        elif isinstance(keys, str):
            normalized_keys = keys.strip()
        else:
            normalized_keys = keys
        data = await super().load(
            (
                normalized_keys,
                class_to_string(where),
                class_to_string(order_by),
                offset,
                limit,
            ),
        )
        if self.filter_method:
            data = self.filter_method(data, self.context)
        return data


def class_to_string(cls: StrawberryType | None) -> str | None:
    """Convert a Strawberry input type instance to its JSON string representation.
    If cls is None, return None.

    Parameters
    ----------
    cls : object | None
        A Strawberry input type instance or None.

    Returns
    -------
    str | None
        A JSON string representation of the object's data if cls is not None,
        otherwise None.

    """
    return json.dumps(asdict(cls), sort_keys=True) if cls else None
