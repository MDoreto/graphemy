from sqlmodel import Field

from graphemy import Dl, Graphemy
import strawberry

def get_cover():
    return "a"

class Album(Graphemy, table=True):
    band_id: int
    id: int = Field(primary_key=True)
    name: str
    musics: list['Music'] = Dl(left='id', right='album_id')

    class Strawberry:
        cover:str = strawberry.field(resolver=get_cover)

