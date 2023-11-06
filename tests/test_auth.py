import pytest
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool


@pytest.fixture
def engine():
    from graphemy import MyModel, Setup

    engine = create_engine(
        'sqlite://',
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
    )

    def get_auth(module, context):
        if module in context['user']['scopes']:
            return True
        return False

    Setup.setup(engine, get_perm=get_auth)
    MyModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def client():
    import strawberry
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from graphemy import MyGraphQLRouter

    class Query:
        @strawberry.field
        async def hello_word(self, info) -> str:
            return 'Hello Word'

    class Mutation:
        @strawberry.field
        async def hello_word(self, info) -> str:
            return 'Hello Word'

    def get_context(request):
        return {'user': {'scopes': ['examples', 'song']}}

    app = FastAPI()
    graphql_app = MyGraphQLRouter(
        query=Query, mutation=Mutation, context_getter=get_context
    )
    app.include_router(graphql_app, prefix='/graphql')
    return TestClient(app)


@pytest.mark.asyncio
async def test_auth_error_children(engine, client):
    from examples.band.band import Band
    from examples.song.song import Song

    band = Band(
        name='Kansas',
    )
    song_1 = Song(
        name='Dust in the Wind',
        band_id=1,
    )

    with Session(engine) as session:
        session.add(song_1)
        session.add(band)
        session.commit()

    query = """
        query TestQuery {
            bands {
                songs {
                    id
                    name

                }
                events{
                    city
                }
            }
        }
    """

    response = client.post('/graphql', json={'query': query})

    assert response.status_code == 403
    assert response.json() == {
        'data': {'bands': []},
        'errors': [
            {
                'message': "User don't have necessary permissions for this path",
                'path': ['band'],
            }
        ],
    }


@pytest.mark.asyncio
async def test_auth_error(engine, client):
    from examples.band.band import Band
    from examples.event.event import Event

    band = Band(
        name='Kansas',
    )
    event = Event(band_id=1, album_id=1, city='Diadema')

    with Session(engine) as session:
        session.add(event)
        session.add(band)
        session.commit()

    query = """
        query TestQuery {
            bands{
                name
            }
            events {
                    city
                }
        }
    """

    response = client.post('/graphql', json={'query': query})

    assert response.status_code == 403
    assert response.json() == {
        'data': {'bands': [], 'events': []},
        'errors': [
            {
                'message': "User don't have necessary permissions for this path",
                'path': ['band', 'event'],
            }
        ],
    }


@pytest.mark.asyncio
async def test_auth(engine, client):
    from examples.song.song import Song
    from examples.word import Word

    song_1 = Song(name='in', band_id=1, album_id=1)
    word = Word(id='in')

    with Session(engine) as session:
        session.add(song_1)
        session.add(word)
        session.commit()

    query = """
        query TestQuery {
                songs{
                    name
                    words{
                        id
                    }
                }
            
        }
    """

    response = client.post('/graphql', json={'query': query})

    assert response.status_code == 200
    assert response.json() == {
        'data': {'songs': [{'name': 'in', 'words': []}]}
    }
