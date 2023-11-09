import pytest


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from examples.query.main import app, engine
    from graphemy import Setup

    Setup.setup(engine=engine)

    return TestClient(app)


@pytest.mark.asyncio
async def test_query(client):
    query = """
            query MyQuery {
                accounts {
                    bankId
                    id
                    modality
                    owner
                }
            }
        """

    response = client.post('/graphql', json={'query': query})

    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'accounts': [
                {
                    'bankId': 1,
                    'id': '12354-6',
                    'modality': 'current',
                    'owner': 'Matheus Doreto',
                },
                {
                    'bankId': 1,
                    'id': '84554-6',
                    'modality': 'saving',
                    'owner': 'Matheus Doreto',
                },
                {
                    'bankId': 1,
                    'id': '15687-6',
                    'modality': 'current',
                    'owner': 'Matheus Doreto',
                },
            ]
        }
    }


@pytest.mark.asyncio
async def test_query_filter(client):
    query = """
            query MyQuery {
                accounts(filters: {modality: "current"}) {
                    bankId
                    id
                    modality
                    owner
                }
            }
        """

    response = client.post('/graphql', json={'query': query})

    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'accounts': [
                {
                    'bankId': 1,
                    'id': '12354-6',
                    'modality': 'current',
                    'owner': 'Matheus Doreto',
                },
                {
                    'bankId': 1,
                    'id': '15687-6',
                    'modality': 'current',
                    'owner': 'Matheus Doreto',
                },
            ]
        }
    }
