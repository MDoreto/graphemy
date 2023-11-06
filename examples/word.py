from graphemy import Field, MyModel, dl, get_list


class Word(MyModel, table=True):
    _default_mutation = True
    _delete_mutation = True
    id: str = Field(primary_key=True)

    @dl('Song')   #
    async def songs(self, info, parameters):
        return await info.context['dl_song_word'].load(self.id, parameters)


async def dl_word_song(keys: list[str]) -> list[Word.schema]:
    return await get_list(Word, keys, contains_fore=True)
