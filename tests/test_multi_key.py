import pytest
from fixture import client


@pytest.mark.asyncio
async def test_query_multi(client):
    query = """
           query MyQuery {
            accounts {
                id
                modality
                customer
                createdAt
                servicesId
                transactions {
                date
                value
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
                    'modality': 'current',
                    'customer': 'Matheus',
                    'createdAt': '2023-02-24',
                    'servicesId': 'insurance, credit',
                    'transactions': [{'date': '2023-02-25', 'value': 100}],
                },
                {
                    'id': '84554-6',
                    'modality': 'saving',
                    'customer': 'Luana',
                    'createdAt': '2023-07-10',
                    'servicesId': '',
                    'transactions': [{'date': '2023-07-15', 'value': 50}],
                },
                {
                    'id': '15687-6',
                    'modality': 'current',
                    'customer': 'Rafael',
                    'createdAt': '2023-09-25',
                    'servicesId': 'insurance',
                    'transactions': [
                        {'date': '2023-11-09', 'value': 200},
                        {'date': '2023-11-10', 'value': -100},
                    ],
                },
            ]
        }
    }


@pytest.mark.asyncio
async def test_multi_parent(client):
    query = """
           query MyQuery {
                transactions {
                    id
                    date
                    value
                    account {
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
            'transactions': [
                {
                    'id': 1,
                    'date': '2023-02-25',
                    'value': 100,
                    'account': {'id': '12354-6', 'bankId': 1},
                },
                {
                    'id': 2,
                    'date': '2023-07-15',
                    'value': 50,
                    'account': {'id': '84554-6', 'bankId': 1},
                },
                {
                    'id': 3,
                    'date': '2023-11-09',
                    'value': 200,
                    'account': {'id': '15687-6', 'bankId': 1},
                },
                {
                    'id': 4,
                    'date': '2023-11-10',
                    'value': -100,
                    'account': {'id': '15687-6', 'bankId': 1},
                },
            ]
        }
    }


@pytest.mark.asyncio
async def test_multi_parent_filter(client):
    query = """
        query MyQuery {
            transactions {
                id
                date
                value
                account(
                filters: {createdAt: {range: ["2023-01-01", "2023-12-01"]}, modality: "saving"}
                ) {
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
            'transactions': [
                {'id': 1, 'date': '2023-02-25', 'value': 100, 'account': None},
                {
                    'id': 2,
                    'date': '2023-07-15',
                    'value': 50,
                    'account': {'id': '84554-6', 'bankId': 1},
                },
                {'id': 3, 'date': '2023-11-09', 'value': 200, 'account': None},
                {
                    'id': 4,
                    'date': '2023-11-10',
                    'value': -100,
                    'account': None,
                },
            ]
        }
    }


@pytest.mark.asyncio
async def test_multi_parent_filter_2(client):
    query = """
        query MyQuery {
            transactions {
                id
                date
                value
                account(
                filters: {createdAt: {range: ["2023-07-01", "2023-12-01"], items: "2023-01-01", year: 2022}, modality: "saving"}
                ) {
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
            'transactions': [
                {'id': 1, 'date': '2023-02-25', 'value': 100, 'account': None},
                {'id': 2, 'date': '2023-07-15', 'value': 50, 'account': None},
                {'id': 3, 'date': '2023-11-09', 'value': 200, 'account': None},
                {
                    'id': 4,
                    'date': '2023-11-10',
                    'value': -100,
                    'account': None,
                },
            ]
        }
    }
