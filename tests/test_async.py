import asyncio

import pytest


@pytest.fixture(scope='module')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_async_put(client_async):
    response = await client_async.post(
        'http://test/graphql',
        json={
            'query': """mutation MyMutation {
                putUser(params: {name: "Some Name", qtd: 10}) {
                    id
                    name
                    qtd
                }
            }"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'data': {'putUser': {'id': 1, 'name': 'Some Name', 'qtd': 10}}
    }


@pytest.mark.asyncio
async def test_async_query(client_async):
    response = await client_async.post(
        'http://test/graphql',
        json={
            'query': """query MyQuery {
                users {
                    id
                    name
                    qtd
                }
            }"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'data': {'users': [{'id': 1, 'name': 'Some Name', 'qtd': 10}]}
    }


@pytest.mark.asyncio
async def test_async_put_with_key(client_async):
    response = await client_async.post(
        'http://test/graphql',
        json={
            'query': """mutation MyMutation {
                putUser(params: {name: "Other Name", id:2, qtd:8}) {
                    id
                }
            }"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {'data': {'putUser': {'id': 2}}}


@pytest.mark.asyncio
async def test_async_update(client_async):
    response = await client_async.post(
        'http://test/graphql',
        json={
            'query': """mutation MyMutation {
                putUser(params: {id:1, name: "Another Name",  qtd: 7}) {
                    id
                    name
                    qtd
                }
            }"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'data': {'putUser': {'id': 1, 'name': 'Another Name', 'qtd': 7}}
    }


@pytest.mark.asyncio
async def test_async_delete(client_async):
    response = await client_async.post(
        'http://test/graphql',
        json={
            'query': """mutation MyMutation {
                deleteUser(params: {id:1}) {
                    id
                }
            }"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {'data': {'deleteUser': {'id': 1}}}
