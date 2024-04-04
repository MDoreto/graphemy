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
    print(response.json())
    assert response.json() == result
