from datetime import date
from sqlmodel import Field, Relationship
from graphemy import Graphemy, dl_test
from typing import List
class Album(Graphemy, table=True):
    band_id: int 
    id: str = Field(primary_key=True)
    release:date
    name:str
    musics:list["Music"] = dl_test(left='id', right='album_id')