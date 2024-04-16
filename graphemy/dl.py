from strawberry.dataloader import DataLoader

from .schemas.models import DateFilter


class Dl:
    source: str | list[str]
    target: str | list[str]
    foreign_key: bool = True

    def __init__(
        self,
        source: str | list[str],
        target: str | list[str],
        foreign_key: bool = True,
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
    def __init__(self, filter_method=None, request=None, **kwargs):
        self.filter_method = filter_method
        self.request = request
        super().__init__(**kwargs)

    async def load(self, keys, filters: dict | None = False):
        if filters == False:
            return await super().load(keys)
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
