from datetime import date

from graphemy import Field, MyModel, dl, get_list


class Event(MyModel, table=True):
    _default_mutation = True
    _delete_mutation = True
    band_id: int = Field(primary_key=True)
    album_id: int = Field(primary_key=True)
    date: date | None
    city: str

    @dl('Song')   #
    async def songs(self, info, parameters):
        return await info.context['dl_song_event'].load(
            [self.band_id, self.album_id], parameters
        )

    @dl('Band')   #
    async def band(self, info, parameters):
        return await info.context['dl_band'].load(self.band_id, parameters)

    @dl('City')
    async def citys(self, info, parameters):
        return await info.context['dl_city_event'].load(self.city, parameters)


async def dl_event_song(keys: list[str]) -> list[Event.schema]:
    return await get_list(Event, keys, ['band_id', 'album_id'])


async def dl_event_band(keys: list[str]) -> list[Event.schema]:
    return await get_list(Event, keys, 'band_id')


async def dl_event_city(keys: list[str]) -> list[Event.schema]:
    return await get_list(Event, keys, 'city', contains=True)
