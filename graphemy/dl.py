from collections.abc import Callable
from dataclasses import asdict
from typing import TYPE_CHECKING, Annotated, TypeVar

from strawberry.dataloader import DataLoader
from strawberry.types.base import StrawberryType

if TYPE_CHECKING:
    from .models import Graphemy

import json


class Dl:
    """
    Represents a mapping between source and target fields used in data loading.

    This class can be used to dynamically construct relationships or references
    between fields (e.g., foreign keys) for Graphemy models. When multiple fields
    are mapped, it ensures the source and target lists match in length and order.

    Attributes:
        source (str | list[str]): The name or list of names of the source fields.
        target (str | list[str]): The name or list of names of the target fields.
        foreign_key (bool | None): Indicates if this mapping involves a foreign key.
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
        """
        Initialize a Dl instance, checking for consistent data types and lengths
        between source and target. If both are lists, they must be the same length.

        Args:
            source (str | list[str]): The source field(s) name(s).
            target (str | list[str]): The target field(s) name(s).
            foreign_key (bool | None, optional): Specifies if the mapping
                is a foreign key relationship. Defaults to None.

        Raises:
            ValueError: If source and target types differ (one is a list while the other
                is a string) or if both are lists of unequal length.
        """
        if type(source) is not type(target):
            raise ValueError("Source and target must have the same type (str or list).")

        # If both source and target are lists, ensure they are the same length and reorder them
        if isinstance(source, list):
            if len(source) != len(target):
                raise ValueError("Source and target lists must have the same length.")

            # Sort the target for consistent ordering, then reorder the source accordingly
            ids = {}
            for i, key in enumerate(target):
                ids[key] = source[i]
            target.sort()
            source = [ids[key] for key in target]

        self.source = source
        self.target = target
        self.foreign_key = foreign_key


ReturnType: TypeVar = (
    list["Graphemy"] | Annotated["Graphemy", ".models"] | None
)
"""
A generic type used for specifying possible return values from GraphemyDataLoader.

- list["Graphemy"]: A list of Graphemy instances.
- Annotated["Graphemy", ".models"]: A single Graphemy instance (with extra annotation).
- None: The data loader can return no value in certain circumstances.
"""


class GraphemyDataLoader(DataLoader):
    """
    A custom data loader for Graphemy models, allowing optional filtering
    and context-aware loading. Inherits from Strawberry's DataLoader.

    This class overrides the load method to handle additional parameters like
    'where', 'order_by', 'offset', and 'limit' for refined data retrieval.
    """

    def __init__(
        self,
        filter_method: Callable[[ReturnType, dict | None], ReturnType] | None = None,
        context: dict | None = None,
        **kwargs: dict,
    ) -> None:
        """
        Initialize the GraphemyDataLoader.

        Args:
            filter_method (Callable[[ReturnType, dict | None], ReturnType] | None, optional):
                A function that applies additional filtering to the loaded data.
                Takes the raw data and the current context as arguments.
                Defaults to None.
            context (dict | None, optional): A dictionary representing the current
                GraphQL context (e.g., request info, user details, etc.). Defaults to None.
            **kwargs: Additional keyword arguments passed to Strawberry's DataLoader.
        """
        self.filter_method = filter_method
        self.context = context
        super().__init__(**kwargs)

    async def load(
        self,
        keys: list,
        where: StrawberryType | None = None,
        order_by: StrawberryType | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> ReturnType:
        """
        Overridden load method to handle extra GraphQL parameters (where, order_by,
        offset, limit) and to optionally apply a custom filter method.

        Args:
            keys (list): A list of keys for which data should be loaded.
            where (StrawberryType | None, optional): A 'where' clause object to filter results.
                Defaults to None.
            order_by (StrawberryType | None, optional): An 'order_by' clause object to sort results.
                Defaults to None.
            offset (int | None, optional): The offset to use when paginating results. Defaults to None.
            limit (int | None, optional): The maximum number of items to fetch (pagination). Defaults to None.

        Returns:
            ReturnType: The loaded data, optionally filtered by filter_method and
                typically in the form of Graphemy instances or None.
        """
        # Normalize keys for the load function
        if isinstance(keys, list):
            normalized_keys = tuple(keys)
        elif isinstance(keys, str):
            normalized_keys = keys.strip()
        else:
            normalized_keys = keys

        # Use the parent load method, passing extra parameters serialized by class_to_string
        data = await super().load(
            (
                normalized_keys,
                class_to_string(where),
                class_to_string(order_by),
                offset,
                limit,
            ),
        )

        # If a filter method is defined, apply it to the resulting data
        if self.filter_method:
            data = self.filter_method(data, self.context)
        return data


def class_to_string(cls: StrawberryType | None) -> str | None:
    """
    Safely serialize a Strawberry (dataclass) instance into a JSON string for use
    in data loader keys or database queries. If no instance is provided, return None.

    Args:
        cls (StrawberryType | None): The Strawberry (dataclass) instance to serialize.

    Returns:
        str | None: The JSON-serialized string representation of the dataclass,
            or None if no class was provided.
    """
    return (
        json.dumps(asdict(cls), sort_keys=True, default=str)
        if cls
        else None
    )
