from strawberry.dataloader import DataLoader
from .schemas.models import DateFilter

class DlModel:
    source: str | list[str]
    target: str | list[str]

    def __init__(self, source: str | list[str], target: str | list[str]):
        self.source = source
        self.target = target


def Dl(source='id', target='id'):
    return DlModel(source, target)

class MyDataLoader(DataLoader):
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
        print(filters)
        data = await super().load(dict_to_tuple(filters))
        print("bbbbbb")
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
