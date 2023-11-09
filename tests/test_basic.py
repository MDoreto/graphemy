import os

import pytest


@pytest.fixture(scope='module')
def client():
    os.environ['GRAPHEMY_PATH'] = 'examples\\query\\models'
    from fastapi.testclient import TestClient

    from examples.tutorial.main import app, engine
    from graphemy import Setup

    Setup.setup(engine=engine)


def test_client(client):
    from fastapi.testclient import TestClient

    from examples.basic.main import app

    client = TestClient(app)

    query = """query MyQuery {
                    helloWorld
                }"""

    response = client.post('/graphql', json={'query': query})

    assert response.json() == {'data': {'helloWorld': 'Hello World'}}
