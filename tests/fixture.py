import pytest


@pytest.fixture(scope='function')
def client():
    from fastapi.testclient import TestClient

    from examples.tutorial.main import app, engine
    from graphemy import Setup

    Setup.setup(engine=engine)

    return TestClient(app)


def check(client, query, result, code=None):
    response = client.post('/graphql', json={'query': query})
    assert response.json() == result
    if code:
        assert response.status_code == code


@pytest.fixture(scope='function')
async def async_client():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy.ext.asyncio import create_async_engine

    from graphemy import Field, Graphemy, GraphemyRouter

    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:',
        echo=False,  # Defina como False se não quiser log de SQL
    )

    class Item(Graphemy, table=True):
        id: int = Field(primary_key=True)
        name: str

    async with engine.begin() as conn:
        await conn.run_sync(Graphemy.metadata.create_all)
        app = FastAPI()
        graphql_app = GraphemyRouter(engine=engine)
        app.include_router(graphql_app, prefix='/graphql')

        return TestClient(app)
