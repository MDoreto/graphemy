import pytest
from sqlmodel import Session

from .fixture import client, engine


@pytest.mark.asyncio
async def test_hello(client):
    query = """
        query testHello {
            helloWord }
    """
    response = client.post('/graphql', json={'query': query})

    # assert response.status_code == 200
    assert response.json() == {'data': {'helloWord': 'Hello Word'}}


@pytest.mark.asyncio
async def test_multi_key_query(engine, client):
    from examples.band.band import Band
    from examples.event.event import Event
    from examples.song.song import Song

    song_1 = Song(name='Dust in the Wind', band_id=1, album_id=1)
    song_2 = Song(name='Carry on my Wayward', band_id=1, album_id=1)
    band = Band(name='Kansas')
    event = Event(band_id=1, album_id=1, city='São Paulo')

    band = Band(name='Kansas')
    with Session(engine) as session:
        session.add(song_1)
        session.add(song_2)
        session.add(event)
        session.add(band)
        session.commit()

    query = """
        query TestQuery {
            events {
                city
                songs {
                    name
                    events{
                        city
                    }
                }
            }
        }
    """

    response = client.post('/graphql', json={'query': query})
    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'events': [
                {
                    'city': 'São Paulo',
                    'songs': [
                        {
                            'name': 'Dust in the Wind',
                            'events': [{'city': 'São Paulo'}],
                        },
                        {
                            'name': 'Carry on my Wayward',
                            'events': [{'city': 'São Paulo'}],
                        },
                    ],
                }
            ]
        }
    }


@pytest.mark.asyncio
async def test_parent_query(engine, client):
    from examples.band.band import Band
    from examples.song.song import Song

    song_1 = Song(
        name='Dust in the Wind',
        band_id=1,
    )
    band = Band(name='Kansas')
    with Session(engine) as session:
        session.add(song_1)
        session.add(band)
        session.commit()

    query = """
        query TestQuery {
            songs(filters:{id: 1}) {
                id
                name
                band{
                    name
                }
            }
        }
    """

    response = client.post('/graphql', json={'query': query})

    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'songs': [
                {
                    'id': 1,
                    'name': 'Dust in the Wind',
                    'band': {'name': 'Kansas'},
                }
            ]
        }
    }
