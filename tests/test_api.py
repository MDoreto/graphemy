import pytest
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from graphemy import MyGraphQLRouter, MyModel, Setup


@pytest.fixture
def engine():
    engine = create_engine(
        'sqlite://',
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
    )
    Setup.setup(
        engine,
        r'.\examples',
    )
    MyModel.metadata.create_all(engine)

    return engine


@pytest.fixture
def client():
    import strawberry
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    class Query:
        @strawberry.field
        async def hello_word(self, info) -> str:
            return 'Hello Word'

    app = FastAPI()
    graphql_app = MyGraphQLRouter(query=Query)
    app.include_router(graphql_app, prefix='/graphql')
    return TestClient(app)


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
    from examples.song import Song

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
    from examples.band import Band
    from examples.song import Song

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
                    'name': 'kansas',
                    'songs': [
                        {'name': 'Dust in the Wind'},
                        {'name': 'Carry on my Wayward'},
                    ],
                }
            ]
        }
    }
