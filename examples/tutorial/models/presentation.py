from graphemy import Dl, Field, Graphemy


class Presentation(Graphemy, table=True):
    album_id: int = Field(primary_key=True)
    year: int = Field(primary_key=True)
    name: str
    event: 'Event' = Dl(
        source=['album_id', 'year'], target=['album_id', 'year']
    )
