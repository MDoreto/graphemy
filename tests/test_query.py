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
async def test_simples_query(engine, client):
    from examples.song.song import Song

    song_1 = Song(
        name='Dust in the Wind',
        band_id=1,
    )

    with Session(engine) as session:
        session.add(song_1)
        session.commit()

    query = """
        query TestQuery {
            songs(filters:{id: 1}) {
                id
                name
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
                }
            ]
        }
    }


@pytest.mark.asyncio
async def test_children_query(engine, client):
    from examples.band.band import Band
    from examples.song.song import Song

    song_1 = Song(
        name='Dust in the Wind',
        band_id=1,
    )
    song_2 = Song(
        name='Carry on my Wayward',
        band_id=1,
    )

    band = Band(name='Kansas')
    with Session(engine) as session:
        session.add(song_1)
        session.add(song_2)
        session.add(band)
        session.commit()

    query = """
        query TestQuery {
            bands {
                id
                name
                songs {
                    name
                }
            }
        }
    """

    response = client.post('/graphql', json={'query': query})

    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'bands': [
                {
                    'id': 1,
                    'name': 'Kansas',
                    'songs': [
                        {'name': 'Dust in the Wind'},
                        {'name': 'Carry on my Wayward'},
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


@pytest.mark.asyncio
async def test_children_filter_query(engine, client):
    from examples.band.band import Band
    from examples.song.song import Song

    song_1 = Song(
        name='Dust in the Wind',
        band_id=1,
    )
    song_2 = Song(
        name='Carry on my Wayward',
        band_id=1,
    )

    band = Band(name='Kansas')
    with Session(engine) as session:
        session.add(song_1)
        session.add(song_2)
        session.add(band)
        session.commit()

    query = """
        query TestQuery {
            bands {
                id
                name
                songs(filters:{id:1}) {
                    name
                }
            }
        }
    """

    response = client.post('/graphql', json={'query': query})

    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'bands': [
                {
                    'id': 1,
                    'name': 'Kansas',
                    'songs': [
                        {'name': 'Dust in the Wind'},
                    ],
                }
            ]
        }
    }


@pytest.mark.asyncio
async def test_children_filter_contains_query(engine, client):
    from examples.city import City
    from examples.event.event import Event

    event = Event(city='Diadema, São Paulo', band_id=1, album_id=1)
    city = City(name='Diadema')

    with Session(engine) as session:
        session.add(event)
        session.add(city)
        session.commit()

    query = """
        query TestQuery {
            events {
                city
                citys {
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
                    'city': 'Diadema, São Paulo',
                    'citys': [
                        {
                            'name': 'Diadema',
                            'events': [{'city': 'Diadema, São Paulo'}],
                        }
                    ],
                }
            ]
        }
    }
