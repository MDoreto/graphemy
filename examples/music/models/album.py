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
        cover_2:str = strawberry.field(resolver=get_cover)
        @strawberry.field
        def cover()-> str:
            return "SSSDASD"

