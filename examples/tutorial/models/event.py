from graphemy import Dl, Field, Graphemy


class Event(Graphemy, table=True):
    album_id: int = Field(primary_key=True)
    year: int = Field(primary_key=True)
    name: str
    presentations: list['Presentation'] = Dl(
        source=['album_id', 'year'], target=['album_id', 'year']
    )
