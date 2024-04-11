from graphemy import Dl, Field, Graphemy


class Member(Graphemy, table=True):
    band_id: int
    id: int = Field(primary_key=True)
    name: str
    role:str
    band: 'Band' = Dl(source='band_id', target='id')
