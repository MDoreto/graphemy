import pytest
import pytest_asyncio

from graphemy import Setup


@pytest.fixture(scope="module")
def clear_classes():
    from sqlmodel.main import default_registry

    from graphemy import Graphemy

    Setup.classes = {}
    Setup.async_engine = False
    Graphemy.metadata.clear()
    default_registry.dispose()
    yield
    Setup.classes = {}
    Setup.async_engine = False
    Graphemy.metadata.clear()
    default_registry.dispose()


@pytest.fixture(scope="module")
def client(clear_classes):
    from fastapi.testclient import TestClient

    from examples.tutorial.basic.main import app, engine

    Setup.setup(engine)
    return TestClient(app)


@pytest.fixture(scope="module")
def client_data(clear_classes):
    import importlib

    from fastapi.testclient import TestClient
    from sqlmodel.main import default_registry

    from examples.tutorial.relationship import main, models
    from graphemy import Graphemy, Setup

    Setup.classes = {}
    Graphemy.metadata.clear()
    default_registry.dispose()

    importlib.reload(models)
    importlib.reload(main)

    return TestClient(main.app)


@pytest_asyncio.fixture(scope="module")
async def client_async(clear_classes):
    from fastapi import FastAPI
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import create_async_engine

    from graphemy import Field, Graphemy, GraphemyRouter

    app = FastAPI()

    engine = create_async_engine(
        "sqlite+aiosqlite:///",
        connect_args={"check_same_thread": False},
    )

    class User(Graphemy, table=True):
        __enable_put_mutation__ = True
        __enable_delete_mutation__ = True
        id: int | None = Field(primary_key=True, default=None)
        name: str
        qtd: int

    async with engine.begin() as conn:
        await conn.run_sync(Graphemy.metadata.create_all)

    router = GraphemyRouter(engine=engine)
    app.include_router(router, prefix="/graphql")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="module")
def client_auth(clear_classes):
    import importlib

    from fastapi.testclient import TestClient
    from sqlmodel.main import default_registry

    from examples.tutorial.auth import main, models
    from graphemy import Graphemy, Setup

    Setup.classes = {}
    Graphemy.metadata.clear()
    default_registry.dispose()

    importlib.reload(models)
    importlib.reload(main)

    return TestClient(main.app)
