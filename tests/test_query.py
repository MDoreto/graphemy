import pytest


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from examples.query.main import app, engine
    from graphemy import Setup

    Setup.setup(engine=engine)

    return TestClient(app)


@pytest.mark.asyncio
async def test_query(client):
    query = """query MyQuery {
                    banks {
                        id
                        name
                        accounts {
                        id
                        modality
                        owner
                        }
                    }
                    }"""

    response = client.post('/graphql', json={'query': query})

    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'banks': [
                {
                    'id': 1,
                    'name': 'Anonymous Bank',
                    'accounts': [
                        {
                            'id': '654654-5',
                            'modality': 'CDB',
                            'owner': 'Matheus Doreto',
                        }
                    ],
                }
            ]
        }
    }
