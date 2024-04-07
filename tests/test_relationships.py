from .fixture import check, client


def test_relationship(client):
    query = """query MyQuery {
                albums {
                  bandId
                  name
                  musics {
                    albumId
                    name
                  }
                }
                musics {
                  albumId
                  name
                  album {
                    name
                  }
                }
              }"""
    result = {
        'data': {
            'albums': [
                {
                    'bandId': 1,
                    'name': 'Leftoverture',
                    'musics': [
                        {'albumId': 1, 'name': 'Miracles of Nowhere'},
                        {'albumId': 1, 'name': 'Miracles of Nowhere'},
                    ],
                }
            ],
            'musics': [
                {
                    'albumId': 1,
                    'name': 'Miracles of Nowhere',
                    'album': {'name': 'Leftoverture'},
                },
                {
                    'albumId': 1,
                    'name': 'Miracles of Nowhere',
                    'album': {'name': 'Leftoverture'},
                },
            ],
        }
    }
    response = client.post('/graphql', json={'query': query})
    assert response.json() == result


def test_relationship_filter(client):
    query = """query MyQuery {
            albums {
              id
              musics(filters: {id: 1}) {
                id
                name
              }
            }
          }"""
    result = {
        'data': {
            'albums': [
                {'id': 1, 'musics': [{'id': 1, 'name': 'Miracles of Nowhere'}]}
            ]
        }
    }
    response = client.post('/graphql', json={'query': query})
    assert response.json() == result
