def test_query(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
                            students {
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
                {"id": 1, "name": "Some Name", "birthDate": "1999-09-16"},
                {"id": 2, "name": "Other Name", "birthDate": "1999-07-24"},
                {"id": 3, "name": "Another Name", "birthDate": "1998-05-12"},
            ],
        },
    }


def test_query_filter(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
                            students (where: {id: {in:1}}){
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
                {"id": 1, "name": "Some Name", "birthDate": "1999-09-16"},
            ],
        },
    }


def test_relationship(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
                            teachers {
                                id
                                name
                                courses {
                                    id
                                    name
                                    }
                                }
                            }""",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "teachers": [
                {
                    "id": 1,
                    "name": "Some Teacher",
                    "courses": [
                        {"id": 1, "name": "Mathematics"},
                        {"id": 2, "name": "Physics"},
                    ],
                },
            ],
        },
    }


def test_relationship_filter(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
                            teachers {
                                id
                                name
                                courses (where: {id: {in:1 } }){
                                    id
                                    name
                                    }
                                }
                            }""",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "teachers": [
                {
                    "id": 1,
                    "name": "Some Teacher",
                    "courses": [
                        {"id": 1, "name": "Mathematics"},
                    ],
                },
            ],
        },
    }


def test_relationship_one(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
  courses {
    id
    name
    teacherId
    teacher {
      id
      name
    }
  }
}
                            """,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "courses": [
                {
                    "id": 1,
                    "name": "Mathematics",
                    "teacherId": 1,
                    "teacher": {"id": 1, "name": "Some Teacher"},
                },
                {
                    "id": 2,
                    "name": "Physics",
                    "teacherId": 1,
                    "teacher": {"id": 1, "name": "Some Teacher"},
                },
            ],
        },
    }


def test_relationship_one_filter(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
  courses {
    id
    name
    teacherId
    teacher (where: {id: { in: 2 } }){
      id
      name
    }
  }
}
                            """,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "courses": [
                {
                    "id": 1,
                    "name": "Mathematics",
                    "teacherId": 1,
                    "teacher": None,
                },
                {"id": 2, "name": "Physics", "teacherId": 1, "teacher": None},
            ],
        },
    }


def test_and(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
  students(where: {AND: {name: {like: "%ther%"}, id: {gte: 2}}}) {
    id
    name
  }
}
                            """,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "students": [
                {
                    "id": 2,
                    "name": "Other Name"
                },
                {
                    "id": 3,
                    "name": "Another Name"
                }
            ]
        }
    }


def test_or(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
  students(where: {OR: {name: {like: "Another%"}, id: {in: 1}}}) {
    id
    name
  }
}
                            """,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "students": [
                {
                    "id": 1,
                    "name": "Some Name"
                },
                {
                    "id": 3,
                    "name": "Another Name"
                }
            ]
        }
    }

def test_not(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
  students(where: {NOT: {name: {like: "%ther%"}}}) {
    id
    name
  }
}
                            """,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
  "data": {
    "students": [
      {
        "id": 1,
        "name": "Some Name"
      }
    ]
  }
}