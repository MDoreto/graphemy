from .fixture import check, client


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
            'albums': [{'bandId': 1, 'id': 1, 'name': 'Dust in the Wind'}],
            'musics': [
                {'albumId': 1, 'id': 1, 'name': 'Dust in the Wind'},
                {'albumId': 1, 'id': 2, 'name': 'Carry on my Wayward'},
            ],
        }
    }
    check(client, query, result)


def test_filter(client):
    query = """query MyQuery {
        musics(filters: {id: 2}) {
            albumId
            id
            name
        }
        }"""
    result = {
        'data': {
            'musics': [{'albumId': 1, 'id': 2, 'name': 'Carry on my Wayward'}]
        }
    }
    check(client, query, result)
