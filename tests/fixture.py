import pytest


@pytest.fixture()
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
