def test_client():
    from fastapi.testclient import TestClient

    from examples.basic.main import app

    client = TestClient(app)

    query = """query MyQuery {
                    helloWorld
                }"""

    response = client.post('/graphql', json={'query': query})

    assert response.json() == {'data': {'helloWorld': 'Hello World'}}
