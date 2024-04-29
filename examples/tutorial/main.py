from datetime import date

from fastapi import FastAPI
from sqlmodel import Session, create_engine, text
from sqlmodel.pool import StaticPool

from graphemy import Graphemy, GraphemyRouter

from .models.album import Album
from .models.band import Band
from .models.event import Event
from .models.member import Member
from .models.music import Music
from .models.presentation import Presentation

engine = create_engine(
    'sqlite://',
    poolclass=StaticPool,
    connect_args={'check_same_thread': False},
)

app = FastAPI()

graphql_app = GraphemyRouter(engine=engine, auto_foreign_keys=True)
app.include_router(graphql_app, prefix='/graphql')


Graphemy.metadata.create_all(engine)

with Session(engine) as session:
    music1 = Music(name='Carry on my Wayward', album_id=1)
    music2 = Music(name='The Wall', album_id=1)
    album1 = Album(name='Leftoverture', band_id=1)
    member1 = Member(
        name='Steve Walsh',
        band_id=1,
        role='singer',
        birthdate=date(1951, 6, 15),
    )
    member2 = Member(
        name='Robby Steinhardt',
        band_id=1,
        role='violin',
        birthdate=date(1950, 5, 25),
    )
    band1 = Band(name='kansas')
    band2 = Band(name='the band')

    presentation = Presentation(album_id=1, year=2012, name='Dust in the Wind')
    event = Event(name='Rock in Rio', album_id=1, year=2012)
    session.add(music1)
    session.add(music2)
    session.add(album1)
    session.add(member1)
    session.add(member2)
    session.add(band1)
    session.add(band2)
    session.add(presentation)
    session.add(event)
    session.commit()
