from sqlmodel import Field

from graphemy import MyModel, dl


class Song(MyModel, table=True):
    id: int | None = Field(primary_key=True)
    name: str
    band_id: int

    @dl('Band', False)   #
    async def band(self, info, parameters):
        return await info.context['dl_band'].load(self.band_id, parameters)
