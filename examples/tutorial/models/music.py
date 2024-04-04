from graphemy import Dl, Field, Graphemy


class Music(Graphemy, table=True):
    __enable_put_mutation__ = True
    __enable_delete_mutation__ = True
    album_id: int
    id: int = Field(primary_key=True)
    name: str
    album: 'Album' = Dl(source='album_id', target='id')
