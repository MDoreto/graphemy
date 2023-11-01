import pytest
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from graphemy import MyGraphQLRouter, MyModel, Setup, schema


class Temp:
    pass


@pytest.mark.asyncio
async def test_hello():
    from graphemy import schema

    query = """
        query testHello {
            helloWord }
    """
    result = await schema.execute(query)
    assert result.errors is None
    assert result.data['helloWord'] == 'Hello Word'


@pytest.mark.asyncio
async def test_query():
    from examples.song import Song

    song_1 = Song(
        name='Dust in the Wind',
        band_id=0,
    )

    engine = create_engine(
        'sqlite://',
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
    )

    MyModel.metadata.create_all(engine)

    Setup.setup(
        engine,
        r'C:\Users\alencma001\OneDrive - Prometeon\Desktop\Projects\graphemy\examples',
    )

    with Session(engine) as session:
        session.add(song_1)
        session.commit()

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    class Query:
        pass

    app = FastAPI()

    graphql_app = MyGraphQLRouter(query=Query)
    app.include_router(graphql_app, prefix='/graphql')

    test_client = TestClient(app)

    query = """
        query TestQuery {
            songs(filters:{id: 1}) {
                id
                name
            }
        }
    """

    response = test_client.post('/graphql', json={'query': query})

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
