from graphemy import Field, MyModel, dl, get_list


class Song(MyModel, table=True):
    _default_mutation = True
    _delete_mutation = True
    id: int | None = Field(primary_key=True)
    name: str
    band_id: int
    album_id: int | None

    @dl('Band', False)   #
    async def band(self, info, parameters):
        return await info.context['dl_band'].load(self.band_id, parameters)

    @dl('Event')   #
    async def events(self, info, parameters):
        return await info.context['dl_event_song'].load(
            [self.band_id, self.album_id], parameters
        )

    @dl('Word')
    async def words(self, info, parameters):
        return await info.context['dl_word_song'].load(self.name, parameters)


async def dl_song_band(keys: list[str]) -> list[Song.schema]:
    return await get_list(Song, keys, 'band_id')


async def dl_song_event(keys: list[str]) -> list[Song.schema]:
    return await get_list(Song, keys, ['band_id', 'album_id'])


async def dl_song_word(keys: list[str]) -> list[Song.schema]:
    return await get_list(Song, keys, 'name', contains=True)
