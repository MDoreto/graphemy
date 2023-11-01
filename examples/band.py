from sqlmodel import Field

from graphemy import MyModel, dl


class Band(MyModel, table=True):
    id: int | None = Field(primary_key=True)
    name: str

    @dl('Song')   #
    async def songs(self, info, parameters):
        return await info.context['dl_song_band'].load(self.id, parameters)
