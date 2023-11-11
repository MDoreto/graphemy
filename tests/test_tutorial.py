import pytest
from fixture import client


@pytest.mark.asyncio
async def test_query(client):
    query = """
           query MyQuery {
            accounts {
            bankId
            id
            modality
            customer
            createdAt
            servicesId
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
                    'customer': 'Matheus',
                    'createdAt': '2023-02-24',
                    'servicesId': 'insurance, credit',
                },
                {
                    'bankId': 1,
                    'id': '84554-6',
                    'modality': 'saving',
                    'customer': 'Luana',
                    'createdAt': '2023-07-10',
                    'servicesId': '',
                },
                {
                    'bankId': 1,
                    'id': '15687-6',
                    'modality': 'current',
                    'customer': 'Rafael',
                    'createdAt': '2023-09-25',
                    'servicesId': 'insurance',
                },
            ]
        }
    }


@pytest.mark.asyncio
async def test_query_filter(client):
    query = """
           query MyQuery {
                accounts(
                    filters: {createdAt: {range: ["2023-07-01", "2023-12-01"]}, modality: "saving"}
                ) {
                    bankId
                    id
                    modality
                    customer
                    createdAt
                    servicesId
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
                    'id': '84554-6',
                    'modality': 'saving',
                    'customer': 'Luana',
                    'createdAt': '2023-07-10',
                    'servicesId': '',
                }
            ]
        }
    }


@pytest.mark.asyncio
async def test_query_filter_2(client):
    query = """
           query MyQuery {
                accounts(
                    filters: {createdAt: { year:2022, items:["2023-07-10"]}, modality: "saving"}
                ) {
                    bankId
                    id
                    modality
                    customer
                    createdAt
                    servicesId
                }
            }
        """

    response = client.post('/graphql', json={'query': query})

    assert response.status_code == 200
    assert response.json() == {'data': {'accounts': []}}
