def test_insert(client):
    response = client.post(
        '/graphql',
        json={
            'query': """mutation MyMutation {
                putStudent(params: {birthDate: "1999-09-16", name: "Some Name"}) {
                    id
                }
            }"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {'data': {'putStudent': {'id': 1}}}


def test_insert_key(client):
    response = client.post(
        '/graphql',
        json={
            'query': """mutation MyMutation {
putStudentCourse(params: {courseId: 1, studentId: 1}) {
    studentId
    courseId
  }
}"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'data': {'putStudentCourse': {'studentId': 1, 'courseId': 1}}
    }


def test_read(client):
    response = client.post(
        '/graphql',
        json={
            'query': """query MyQuery {
                students {
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
                {'birthDate': '1999-09-16', 'id': 1, 'name': 'Some Name'}
            ]
        }
    }


def test_update(client):
    response = client.post(
        '/graphql',
        json={
            'query': """mutation MyMutation {
                putStudent(params: {birthDate: "1999-09-16", name: "Some Name Last", id: 1}) {
                    id
                    name
                }
            }"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'data': {'putStudent': {'id': 1, 'name': 'Some Name Last'}}
    }
    response = client.post(
        '/graphql',
        json={
            'query': """query MyQuery {
                students {
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
                {'birthDate': '1999-09-16', 'id': 1, 'name': 'Some Name Last'}
            ]
        }
    }


def test_delete(client):
    response = client.post(
        '/graphql',
        json={
            'query': """mutation MyMutation {
                deleteStudent(params: {id: 1}) {
                    id
                }
            }"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {'data': {'deleteStudent': {'id': 1}}}
    response = client.post(
        '/graphql',
        json={
            'query': """query MyQuery {
                students {
                    id
                    name
                    birthDate
                }
            }"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {'data': {'students': []}}
