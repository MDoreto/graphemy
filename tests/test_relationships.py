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


def test_filter_date_year(client):
    query = """query MyQuery {
  members(filters: {birthdate: {year: 1951}}) {
    name
    id
  }
}"""
    result = {'data': {'members': [{'name': 'Steve Walsh', 'id': 1}]}}
    response = client.post('/graphql', json={'query': query})
    assert response.json() == result


def test_filter_date_items(client):
    query = """query MyQuery {
  members(filters: {birthdate: {items: "1950-05-25"}}) {
    name
    id
    birthdate
  }
}"""
    result = {
        'data': {
            'members': [
                {
                    'name': 'Robby Steinhardt',
                    'id': 2,
                    'birthdate': '1950-05-25',
                }
            ]
        }
    }
    response = client.post('/graphql', json={'query': query})
    assert response.json() == result


def test_filter_date_range(client):
    query = """query MyQuery {
  members(filters: {birthdate: {range: ["1949-05-24","1952-05-27"]}}) {
    name
    id
    birthdate
  }
}"""
    result = {
        'data': {
            'members': [
                {'name': 'Steve Walsh', 'id': 1, 'birthdate': '1951-06-15'},
                {
                    'name': 'Robby Steinhardt',
                    'id': 2,
                    'birthdate': '1950-05-25',
                },
            ]
        }
    }
    response = client.post('/graphql', json={'query': query})
    assert response.json() == result


def test_filter_dl_date(client):
    query = """query MyQuery {
  bands {
    name
    members(filters: {birthdate: {items: "1951-06-15", year: 1950, range: ["1941-06-15","1961-06-15"]}}) {
      id
      name
      birthdate
    }
    id
  }
}"""
    result = {
        'data': {
            'bands': [
                {'name': 'kansas', 'members': [], 'id': 1},
                {'name': 'the band', 'members': [], 'id': 2},
            ]
        }
    }
    response = client.post('/graphql', json={'query': query})
    assert response.json() == result


def test_dl_filter_multi(client):
    query = """query MyQuery {
  bands {
    name
    members(filters: {id: 1}) {
      id
      name
      birthdate
      band(filters: {id: 2}) {
        id
      }
    }
    id
  }
  teste: bands {
    name
    members(filters: {id: 2}) {
      id
      name
      birthdate
      band(filters: {id: 1}) {
        id
      }
    }
    id
  }
}"""
    result = {
        'data': {
            'bands': [
                {
                    'name': 'kansas',
                    'members': [
                        {
                            'id': 1,
                            'name': 'Steve Walsh',
                            'birthdate': '1951-06-15',
                            'band': None,
                        }
                    ],
                    'id': 1,
                },
                {'name': 'the band', 'members': [], 'id': 2},
            ],
            'teste': [
                {
                    'name': 'kansas',
                    'members': [
                        {
                            'id': 2,
                            'name': 'Robby Steinhardt',
                            'birthdate': '1950-05-25',
                            'band': {'id': 1},
                        }
                    ],
                    'id': 1,
                },
                {'name': 'the band', 'members': [], 'id': 2},
            ],
        }
    }
    response = client.post('/graphql', json={'query': query})
    assert response.json() == result
