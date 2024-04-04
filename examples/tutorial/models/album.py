from graphemy import Dl, Field, Graphemy


class Album(Graphemy, table=True):
    band_id: int
    id: int = Field(primary_key=True)
    name: str
    musics: list['Music'] = Dl(source='id', target='album_id')
