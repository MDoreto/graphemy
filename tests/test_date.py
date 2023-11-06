import pytest
from sqlmodel import Session

from .fixture import client, engine


@pytest.fixture
def db(engine):
    from datetime import date

    from examples.band.band import Band
    from examples.event.event import Event

    event = Event(
        band_id=1,
        album_id=1,
        city='São Paulo',
        date=date(2023, 9, 16),
    )
    event_2 = Event(
        band_id=1,
        album_id=2,
        date=date(2022, 7, 24),
        city='Fortaleza',
    )
    event_3 = Event(
        band_id=1,
        album_id=3,
        date=date(2022, 11, 1),
        city='Barcelona',
    )

    band = Band(name='Kansas')
    with Session(engine) as session:
        session.add(event)
        session.add(event_2)
        session.add(event_3)
        session.add(band)
        session.commit()

    return True


@pytest.mark.asyncio
async def test_date_year(db, client):

    query = """
        query TestQuery {
            events (filters:{date: {year: 2023}}) {
                city
                date
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
                    'date': '2023-09-16',
                }
            ]
        }
    }


@pytest.mark.asyncio
async def test_date_year_children(db, client):

    query = """
        query TestQuery {
            bands {
                name
                events (filters:{date: {year: 2023}}) {
                    city
                    date
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
                    'name': 'Kansas',
                    'events': [
                        {
                            'city': 'São Paulo',
                            'date': '2023-09-16',
                        }
                    ],
                }
            ]
        }
    }


@pytest.mark.asyncio
async def test_date_range(db, client):

    query = """
        query TestQuery {
            events (filters:{date: {range: ["2022-10-01","2023-10-01"]}}) {
                city
                date
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
                    'date': '2023-09-16',
                },
                {
                    'city': 'Barcelona',
                    'date': '2022-11-01',
                },
            ]
        }
    }


@pytest.mark.asyncio
async def test_date_range_children(db, client):

    query = """
        query TestQuery {
            bands {
                name
                events (filters:{date: {range: ["2022-10-01","2023-10-01"]}}) {
                    city
                    date
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
                    'name': 'Kansas',
                    'events': [
                        {
                            'city': 'São Paulo',
                            'date': '2023-09-16',
                        },
                        {
                            'city': 'Barcelona',
                            'date': '2022-11-01',
                        },
                    ],
                }
            ]
        }
    }


@pytest.mark.asyncio
async def test_date_items(db, client):

    query = """
        query TestQuery {
            events (filters:{date: {items:["2022-11-01","2022-07-24","2023-01-01"]}}) {
                city
                date
            }
        }
    """

    response = client.post('/graphql', json={'query': query})

    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'events': [
                {
                    'city': 'Fortaleza',
                    'date': '2022-07-24',
                },
                {
                    'city': 'Barcelona',
                    'date': '2022-11-01',
                },
            ]
        }
    }


@pytest.mark.asyncio
async def test_date_items_children(db, client):

    query = """
        query TestQuery {
            bands {
                name
                events (filters:{date: {items:["2022-11-01","2022-07-24","2023-01-01"]}}) {
                    city
                    date
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
                    'name': 'Kansas',
                    'events': [
                        {
                            'city': 'Fortaleza',
                            'date': '2022-07-24',
                        },
                        {
                            'city': 'Barcelona',
                            'date': '2022-11-01',
                        },
                    ],
                }
            ]
        }
    }
