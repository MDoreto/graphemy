def test_date_year(client_data):
    response = client_data.post(
        '/graphql',
        json={
            'query': """query MyQuery {
                            students (filters: {birthDate: {year: 1999}}){
                                id
                                name
                                birthDate
                                }
                            }"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'students': [
                {'id': 1, 'name': 'Some Name', 'birthDate': '1999-09-16'},
                {'id': 2, 'name': 'Other Name', 'birthDate': '1999-07-24'},
            ]
        }
    }


def test_date_range(client_data):
    response = client_data.post(
        '/graphql',
        json={
            'query': """query MyQuery {
                            students (filters: {birthDate: {range: ["1998-04-01","1999-08-25"]}}) {
                                id
                                name
                                birthDate
                                }
                            }"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'students': [
                {'id': 2, 'name': 'Other Name', 'birthDate': '1999-07-24'},
                {'id': 3, 'name': 'Another Name', 'birthDate': '1998-05-12'},
            ]
        }
    }


def test_date_items(client_data):
    response = client_data.post(
        '/graphql',
        json={
            'query': """query MyQuery {
                            students (filters: {birthDate: {items: "1999-09-16"}}){
                                id
                                name
                                birthDate
                                }
                            }"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'students': [
                {'id': 1, 'name': 'Some Name', 'birthDate': '1999-09-16'},
            ]
        }
    }


def test_date_nested_year(client_data):
    response = client_data.post(
        '/graphql',
        json={
            'query': """query MyQuery {
  courses {
    id
    name
    teacherId
    students {
      student(filters: {birthDate: {year: 1998}}) {
        name
      }
    }
  }
}"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'courses': [
                {
                    'id': 1,
                    'name': 'Mathematics',
                    'teacherId': 1,
                    'students': [
                        {'student': None},
                        {'student': None},
                        {'student': {'name': 'Another Name'}},
                    ],
                },
                {
                    'id': 2,
                    'name': 'Physics',
                    'teacherId': 1,
                    'students': [{'student': None}, {'student': None}],
                },
            ]
        }
    }


def test_date_nested_range(client_data):
    response = client_data.post(
        '/graphql',
        json={
            'query': """query MyQuery {
  courses {
    id
    name
    teacherId
    students {
      student(filters: {birthDate: {range: ["1999-08-01","1999-10-25"]}}) {
        name
      }
    }
  }
}"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'courses': [
                {
                    'id': 1,
                    'name': 'Mathematics',
                    'teacherId': 1,
                    'students': [
                        {'student': {'name': 'Some Name'}},
                        {'student': None},
                        {'student': None},
                    ],
                },
                {
                    'id': 2,
                    'name': 'Physics',
                    'teacherId': 1,
                    'students': [
                        {'student': {'name': 'Some Name'}},
                        {'student': None},
                    ],
                },
            ]
        }
    }


def test_date_nested_items(client_data):
    response = client_data.post(
        '/graphql',
        json={
            'query': """query MyQuery {
  courses {
    id
    name
    teacherId
    students {
      student(filters: {birthDate: {items: ["1999-07-24"]}}) {
        name
      }
    }
  }
}"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'courses': [
                {
                    'id': 1,
                    'name': 'Mathematics',
                    'teacherId': 1,
                    'students': [
                        {'student': None},
                        {'student': {'name': 'Other Name'}},
                        {'student': None},
                    ],
                },
                {
                    'id': 2,
                    'name': 'Physics',
                    'teacherId': 1,
                    'students': [
                        {'student': None},
                        {'student': {'name': 'Other Name'}},
                    ],
                },
            ]
        }
    }
