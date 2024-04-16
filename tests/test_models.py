import pytest

from .fixture import async_client, check, client


def test_query(client):
    query = """query MyQuery {
                    albums {
                        bandId
                        id
                        name
                    }
                    musics {
                        albumId
                        id
                        name
                    }
                }"""
    result = {
        'data': {
            'albums': [{'bandId': 1, 'id': 1, 'name': 'Leftoverture'}],
            'musics': [
                {'albumId': 1, 'id': 1, 'name': 'Carry on my Wayward'},
                {'albumId': 1, 'id': 2, 'name': 'The Wall'},
            ],
        }
    }
    check(client, query, result)


def test_filter(client):
    query = """query MyQuery {
        musics(filters: {id: 1}) {
            albumId
            id
            name
        }
        }"""
    result = {
        'data': {
            'musics': [{'albumId': 1, 'id': 1, 'name': 'Carry on my Wayward'}]
        }
    }
    check(client, query, result)


def test_insert(client):
    query = """mutation MyMutation {
  putMusic(params: {albumId: 1, name: "Miracles of Nowhere"}) {
    albumId
    id
    name
  }
}"""
    result = {
        'data': {
            'putMusic': {'albumId': 1, 'id': 3, 'name': 'Miracles of Nowhere'}
        }
    }
    check(client, query, result)


def test_update(client):
    query = """mutation MyMutation {
        putMusic(params: {id: 1, albumId: 1, name: "Miracles of Nowhere"}) {
            albumId
            id
            name
        }
        }"""
    result = {
        'data': {
            'putMusic': {'albumId': 1, 'id': 1, 'name': 'Miracles of Nowhere'}
        }
    }
    check(client, query, result)


def test_delete(client):
    query = """mutation MyMutation {
        deleteMusic(params: {id: 2}) {
            albumId
            id
            name
        }
        }"""
    result = {
        'data': {'deleteMusic': {'albumId': 1, 'id': 2, 'name': 'The Wall'}}
    }
    check(client, query, result)


# @pytest.mark.asyncio
# async def test_async_insert(async_client):
#     query = """mutation MyMutation {
#   putItem(params: {name: "Music"}) {
#     id
#     name
#   }
# }"""
#     result = {'data': {'putItem': {'id': 1, 'name': 'Music'}}}
#     temp = await async_client
#     response = temp.post('/graphql', json={'query': query})
#     assert response.json() == result
