from sqlmodel import Field
from graphemy import Dl, Graphemy


class Music(Graphemy, table=True):
    album_id: int 
    id: int = Field(primary_key=True)
    name: str
    album: 'Album' = Dl(source='album_id', target='id')
