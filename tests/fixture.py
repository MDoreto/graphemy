import pytest
from sqlmodel import create_engine
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

    class Mutation:
        @strawberry.field
        async def hello_word(self, info) -> str:
            return 'Hello Word'

    app = FastAPI()
    graphql_app = MyGraphQLRouter(query=Query, mutation=Mutation)
    app.include_router(graphql_app, prefix='/graphql')
    return TestClient(app)
