def test_pagination(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
  students(offset: 1, limit: 2) {
    id
    name
    birthDate
  }
}""",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "students": [
                {
                    "id": 2,
                    "name": "Other Name",
                    "birthDate": "1999-07-24"
                },
                {
                    "id": 3,
                    "name": "Another Name",
                    "birthDate": "1998-05-12"
                }
            ],
            "studentsCount": 3
        }
    }


def test_pagination_dl(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
  schools {
    students(limit: 1, offset: 2) {
      name
    }
    name
  }
}""",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "schools": [
                {
                    "students": [
                        {
                            "name": "Another Name"
                        }
                    ],
                    "name": "Some School",
                    "studentsCount": 3
                }
            ]
        }
    }
