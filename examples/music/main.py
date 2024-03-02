from fastapi import FastAPI
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from graphemy import Graphemy, GraphemyRouter

from .models.album import Album
from .models.music import Music

engine = create_engine(
    'sqlite://',
    poolclass=StaticPool,
    connect_args={'check_same_thread': False},
)

app = FastAPI()

graphql_app = GraphemyRouter(engine=engine)
app.include_router(graphql_app, prefix='/graphql')

Graphemy.metadata.create_all(engine)

with Session(engine) as session:
    music1 = Music(name='Dust in the Wind', album_id=1)
    music2 = Music(name='Carry on my Wayward', album_id=1)
    album1 = Album(name='Dust in the Wind', band_id=1)
    session.add(music1)
    session.add(music2)
    session.add(album1)
    session.commit()
