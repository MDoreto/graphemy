from graphemy import Dl, Field, Graphemy


class Band(Graphemy, table=True):
    id: int = Field(primary_key=True)
    name: str
    albums: list['Album'] = Dl(source='id', target='band_id')
    members: list['Member'] = Dl(source='id', target='band_id')
