import pytest
from fixture import client


@pytest.mark.asyncio
async def test_no_dl(client):
    query = """
           query MyQuery {
                banks {
                    id
                    externalField
                }
            }
        """

    response = client.post('/graphql', json={'query': query})
    assert response.status_code == 200
    assert response.json() == {
        'data': {'banks': [{'id': 1, 'externalField': 'Put you logic her'}]}
    }


@pytest.mark.asyncio
async def test_no_foreign_key(client):
    from datetime import date

    from sqlmodel import Session

    from examples.tutorial.main import engine
    from examples.tutorial.models.transaction import Transaction

    with Session(engine) as session:
        transaction = Transaction(
            bank_id=None, account_id=None, value=10, date=date(2023, 7, 10)
        )
        session.add(transaction)
        session.commit()

    query = """
           query MyQuery {
                transactions (filters: { id: 5}){
                    id
                    account {
                        id
                    }
                    bank{
                        id
                    }
                }
            }
        """

    response = client.post('/graphql', json={'query': query})
    assert response.status_code == 200
    assert response.json() == {
        'data': {'transactions': [{'id': 5, 'account': None, 'bank': None}]}
    }


@pytest.mark.asyncio
async def test_multi_dl_same_level(client):
    query = """
           query MyQuery {
                banksSaving:banks {
                    id
                    accounts(
                    filters: { modality: "saving"}
                    ) {
                    id
                    }
                }
                banksCurrent:banks {
                    id
                    accounts(
                    filters: { modality: "current"}
                    ) {
                    id
                    }
                }
            }
        """
    response = client.post('/graphql', json={'query': query})
    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'banksSaving': [{'id': 1, 'accounts': [{'id': '84554-6'}]}],
            'banksCurrent': [
                {'id': 1, 'accounts': [{'id': '12354-6'}, {'id': '15687-6'}]}
            ],
        }
    }


@pytest.mark.asyncio
async def test_multi_dl_same_level_parent(client):
    query = """
           query MyQuery {
                accounts1:accounts {
                    id
                    bank(
                    filters: { id: 1}
                    ) {
                    id
                    }
                }
                accounts2:accounts {
                    id
                    bank(
                    filters: { id: 2}
                    ) {
                    id
                    }
                }
            }
        """
    response = client.post('/graphql', json={'query': query})
    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'accounts1': [
                {'id': '12354-6', 'bank': {'id': 1}},
                {'id': '84554-6', 'bank': {'id': 1}},
                {'id': '15687-6', 'bank': {'id': 1}},
            ],
            'accounts2': [
                {'id': '12354-6', 'bank': None},
                {'id': '84554-6', 'bank': None},
                {'id': '15687-6', 'bank': None},
            ],
        }
    }


@pytest.mark.asyncio
async def test_graphql_error(client):
    query = """
           query MyQuery {
                bank {
                    id
                }
                
            }
        """
    response = client.post('/graphql', json={'query': query})
    assert response.status_code == 200
    assert response.json() == {
        'data': None,
        'errors': [
            {
                'message': "Cannot query field 'bank' on type 'Query'. Did you mean 'banks'?",
                'locations': [{'line': 3, 'column': 17}],
            }
        ],
    }


@pytest.mark.asyncio
async def test_graphql_no_filter(client):
    query = """
           query MyQuery {
                banks (filters: null) {
                    id
                    customDl 
                }
                
            }
        """
    response = client.post('/graphql', json={'query': query})
    assert response.status_code == 200
    assert response.json() == {'data': {'banks': [{'id': 1, 'customDl': 1}]}}


@pytest.mark.asyncio
async def test_mutation_put_id(client):
    mutation = """
           mutation MyMutation {
                putBank(params: {id: 3, code: 3, name: "New Bank with id"}) {
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
                {'code': 3, 'id': 3, 'name': 'New Bank with id'},
            ]
        }
    }
