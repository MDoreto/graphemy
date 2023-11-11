import pytest
from fixture import client


@pytest.mark.asyncio
async def test_relationship_children(client):
    query = """
           query MyQuery {
                banks {
                    id
                    name
                    code
                    accounts {
                    id
                    customer
                    }
                }
            }
        """

    response = client.post('/graphql', json={'query': query})

    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'banks': [
                {
                    'id': 1,
                    'name': 'Anonymous',
                    'code': 1,
                    'accounts': [
                        {'id': '12354-6', 'customer': 'Matheus'},
                        {'id': '15687-6', 'customer': 'Rafael'},
                        {'id': '84554-6', 'customer': 'Luana'},
                    ],
                }
            ]
        }
    }


@pytest.mark.asyncio
async def test_relationship_filter(client):
    query = """
           query MyQuery {
                banks {
                    id
                    name
                    code
                    accounts(
                    filters: {createdAt: {range: ["2023-07-01", "2023-12-01"]}, modality: "saving"}
                    ) {
                    id
                    customer
                    }
                }
            }
        """

    response = client.post('/graphql', json={'query': query})

    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'banks': [
                {
                    'id': 1,
                    'name': 'Anonymous',
                    'code': 1,
                    'accounts': [{'id': '84554-6', 'customer': 'Luana'}],
                }
            ]
        }
    }


@pytest.mark.asyncio
async def test_relationship_filter_2(client):
    query = """
           query MyQuery {
                banks {
                    id
                    name
                    code
                    accounts(
                    filters: {createdAt: {range: ["2023-07-01", "2023-12-01"], items: "2023-01-01", year: 2022}, modality: "saving"}
                    ) {
                    id
                    customer
                    createdAt
                    }
                }
            }
        """

    response = client.post('/graphql', json={'query': query})

    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'banks': [
                {'id': 1, 'name': 'Anonymous', 'code': 1, 'accounts': []}
            ]
        }
    }
