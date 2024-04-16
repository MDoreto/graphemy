from fastapi import FastAPI
from sqlmodel import Session, create_engine, text
from sqlmodel.pool import StaticPool

from graphemy import Graphemy, GraphemyRouter

from .models.album import Album
from .models.music import Music
from .models.band import Band
from .models.member import Member
engine = create_engine(
    'sqlite://',
    poolclass=StaticPool,
    connect_args={'check_same_thread': False},
)

app = FastAPI()

graphql_app = GraphemyRouter(engine=engine,auto_foreign_keys=True)
app.include_router(graphql_app, prefix='/graphql')


Graphemy.metadata.create_all(engine)

with Session(engine) as session:
    music1 = Music(name='Carry on my Wayward', album_id=1)
    music2 = Music(name='The Wall', album_id=1)
    album1 = Album(name='Leftoverture', band_id=1)
    member1 = Member(name='Steve Walsh', band_id=1, role='singer')
    band1 = Band(name='kansas')
    session.add(music1)
    session.add(music2)
    session.add(album1)
    session.add(member1)
    session.add(band1)
    session.commit()
