def test_sort(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
  students(orderBy: {id: desc}) {
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
                    "id": 3,
                    "name": "Another Name",
                    "birthDate": "1998-05-12"
                },
                {
                    "id": 2,
                    "name": "Other Name",
                    "birthDate": "1999-07-24"
                },
                {
                    "id": 1,
                    "name": "Some Name",
                    "birthDate": "1999-09-16"
                }
            ]
        }
    }


def test_sort_asc(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
  students(orderBy: {id: asc}) {
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
                    "id": 1,
                    "name": "Some Name",
                    "birthDate": "1999-09-16"
                },
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
            ]
        }
    }


def test_sort_dl(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
  schools {
    students(orderBy: {birthDate: desc}) {
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
                            "name": "Some Name"
                        },
                        {
                            "name": "Other Name"
                        },
                        {
                            "name": "Another Name"
                        }
                    ],
                    "name": "Some School"
                }
            ]
        }
    }
