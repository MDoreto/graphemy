from graphemy import Field, MyModel, dl, get_list


class City(MyModel, table=True):
    name: str = Field(primary_key=True)

    @dl('Event')   #
    async def events(self, info, parameters):
        return await info.context['dl_event_city'].load(self.name, parameters)


async def dl_city_event(keys: list[str]) -> list[City.schema]:
    return await get_list(City, keys, id='name', contains_fore=True)
