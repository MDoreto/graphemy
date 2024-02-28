from datetime import date
from sqlmodel import Field, Relationship
from graphemy import Graphemy, dl_test

class Music(Graphemy, table=True):
    album_id: int 
    id: str = Field(primary_key=True)
    name:str
    lyrics:str
    album:"Album" = dl_test(left='album_id', right='id')