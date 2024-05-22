from strawberry.dataloader import DataLoader

from .schemas.models import DateFilter


class Dl:
    """
    A utility class designed to facilitate the linking of source and target fields
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
        foreign_key: bool = None,
    ):
        if type(source) != type(target):
            raise 'source and target must have same type'
        if type(source) == list:
            if len(source) != len(target):
                raise 'source and target must have same length'
            ids = {}
            for i, id in enumerate(target):
                ids[id] = source[i]
            target.sort()
            source = [ids[id] for id in target]
        self.source = source
        self.target = target
        self.foreign_key = foreign_key


class GraphemyDataLoader(DataLoader):
    """
    A customized DataLoader that handles additional filtering mechanisms during data
    retrieval processes. It is capable of using predefined filter methods to process data
    based on request-specific parameters.

    Attributes:
        filter_method (callable): A method that applies additional filtering to the data
            based on the request context and specified filters.
        request: The context of the request, used to pass additional parameters to the
            filter_method.

    Methods:
        load: Overridden to apply filters before returning the data, enhancing the
            DataLoader's functionality to cater to complex querying needs.
    """

    def __init__(self, filter_method=None, request=None, **kwargs):
        self.filter_method = filter_method
        self.request = request
        super().__init__(**kwargs)

    async def load(self, keys, filters: dict | None):
        filters['keys'] = (
            tuple(keys)
            if isinstance(keys, list)
            else keys.strip()
            if isinstance(keys, str)
            else keys
        )
        data = await super().load(dict_to_tuple(filters))
        if self.filter_method:
            data = self.filter_method(data, self.request)
        return data


def dict_to_tuple(data: dict) -> tuple:
    """
    Converts a dictionary into a tuple, recursively processing nested dictionaries
    and lists to ensure they are in a hashable and comparable format. This is essential
    for caching mechanisms within DataLoaders.

    Args:
        data (dict): The dictionary to be converted.

    Returns:
        tuple: A tuple representation of the original dictionary, suitable for use as
            a key in caching operations.
    """
    result = []
    for key, value in data.items():
        if isinstance(value, DateFilter):
            value = vars(value)
        if isinstance(value, dict):
            nested_tuples = dict_to_tuple(value)
            result.append((key, nested_tuples))
        elif isinstance(value, list):
            nested_tuples = tuple(
                sorted(
                    dict_to_tuple(item)
                    if isinstance(item, dict) or isinstance(item, DateFilter)
                    else item
                    for item in value
                )
            )
            result.append((key, nested_tuples))
        else:
            result.append((key, value))
    return tuple(sorted(result))
