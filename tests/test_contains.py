import pytest
from fixture import client


@pytest.mark.asyncio
async def test_query_contains(client):
    query = """
           query MyQuery {
                accounts {
                    id
                    customer
                    servicesId
                    services {
                    description
                    id
                    }
                }
            }
        """

    response = client.post('/graphql', json={'query': query})

    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'accounts': [
                {
                    'id': '12354-6',
                    'customer': 'Matheus',
                    'servicesId': 'insurance, credit',
                    'services': [
                        {'description': 'some description', 'id': 'insurance'},
                        {'description': 'some description', 'id': 'credit'},
                    ],
                },
                {
                    'id': '84554-6',
                    'customer': 'Luana',
                    'servicesId': '',
                    'services': [],
                },
                {
                    'id': '15687-6',
                    'customer': 'Rafael',
                    'servicesId': 'insurance',
                    'services': [
                        {'description': 'some description', 'id': 'insurance'}
                    ],
                },
            ]
        }
    }


@pytest.mark.asyncio
async def test_contains_parent(client):
    query = """
          query MyQuery {
  servicess {
    description
    id
    accounts {
      id
      bankId
    }
  }
}
        """

    response = client.post('/graphql', json={'query': query})

    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'servicess': [
                {
                    'description': 'some description',
                    'id': 'insurance',
                    'accounts': [
                        {'id': '12354-6', 'bankId': 1},
                        {'id': '15687-6', 'bankId': 1},
                    ],
                },
                {
                    'description': 'some description',
                    'id': 'credit',
                    'accounts': [{'id': '12354-6', 'bankId': 1}],
                },
            ]
        }
    }
