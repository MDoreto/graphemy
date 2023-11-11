import pytest


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from examples.tutorial.main import app, engine
    from graphemy import Setup

    def get_permission(module, context):
        return 'account' in module

    Setup.setup(engine=engine, get_perm=get_permission)

    return TestClient(app)


@pytest.mark.asyncio
async def test_permission_query(client):

    query = """
        query MyQuery {
            banks {
                code
                id
                name
            }
        }
    """

    response = client.post('/graphql', json={'query': query})
    assert response.status_code == 403
    assert response.json() == {
        'data': {'banks': []},
        'errors': [
            {
                'message': "User don't have necessary permissions for this path",
                'path': ['examples\\tutorial\\models\\bank.py'],
            }
        ],
    }


@pytest.mark.asyncio
async def test_permission_query(client):

    query = """
        query MyQuery {
                accounts {
                    id
                    services {
                    description
                    id
                    }
                    transactions{
                    id
                    }
                    bank{
                    id
                    }

                }
            }
    """

    response = client.post('/graphql', json={'query': query})
    assert response.status_code == 403
    assert response.json() == {
        'data': {
            'accounts': [
                {
                    'id': '12354-6',
                    'services': [],
                    'transactions': [],
                    'bank': None,
                },
                {
                    'id': '84554-6',
                    'services': [],
                    'transactions': [],
                    'bank': None,
                },
                {
                    'id': '15687-6',
                    'services': [],
                    'transactions': [],
                    'bank': None,
                },
            ]
        },
        'errors': [
            {
                'message': "User don't have necessary permissions for this path",
                'path': [
                    'examples\\tutorial\\models\\services',
                    'examples\\tutorial\\models\\transaction',
                    'examples\\tutorial\\models\\bank',
                ],
            }
        ],
    }
