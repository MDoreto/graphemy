import pytest


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from examples.tutorial.main import app, engine
    from graphemy import Setup

    Setup.setup(engine=engine)

    return TestClient(app)
