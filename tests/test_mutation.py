import pytest
from fixture import client


@pytest.mark.asyncio
async def test_mutation(client):
    mutation = """
           mutation MyMutation {
                putBank(params: {code: 2, name: "New Bank"}) {
                    id
                    name
                    code
                }
            }
        """
    client.post('/graphql', json={'query': mutation})

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

    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'banks': [
                {'code': 1, 'id': 1, 'name': 'Anonymous'},
                {'code': 2, 'id': 2, 'name': 'New Bank'},
            ]
        }
    }


@pytest.mark.asyncio
async def test_mutation_edit(client):
    mutation = """
          mutation MyMutation {
                putBank(params: {id: 2, code: 2, name: "Updated Bank"}) {
                    id
                    name
                    code
                }
            }
        """

    client.post('/graphql', json={'query': mutation})

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

    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'banks': [
                {'code': 1, 'id': 1, 'name': 'Anonymous'},
                {'code': 2, 'id': 2, 'name': 'Updated Bank'},
            ]
        }
    }


@pytest.mark.asyncio
async def test_delete(client):
    query = """
          mutation MyMutation {
                deleteBank(params: {id: 2}) {
                    code
                    id
                    name
                }
            }
        """

    client.post('/graphql', json={'query': query})

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

    assert response.status_code == 200
    assert response.json() == {
        'data': {'banks': [{'code': 1, 'id': 1, 'name': 'Anonymous'}]}
    }
