from sqlmodel import Field

from graphemy import MyModel, dl, get_list


class Song(MyModel, table=True):
    id: int | None = Field(primary_key=True)
    name: str
    band_id: int

    @dl('Band', False)   #
    async def band(self, info, parameters):
        return await info.context['dl_band'].load(self.band_id, parameters)


async def dl_song_band(keys: list[str]) -> list[Song.schema]:
    return await get_list(Song, keys)
