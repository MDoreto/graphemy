from graphemy import Field, MyModel, dl, get_one


class Band(MyModel, table=True):
    _default_mutation = True
    _delete_mutation = True
    id: int | None = Field(primary_key=True)
    name: str

    @dl('Song')   #
    async def songs(self, info, parameters):
        return await info.context['dl_song_band'].load(self.id, parameters)

    @dl('Event')   #
    async def events(self, info, parameters):
        return await info.context['dl_event_band'].load(self.id, parameters)


async def dl_band(keys: list[str]) -> Band.schema:
    return await get_one(Band, keys)
