def test_multi_query(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
  teachers {
    id
    name
    courses(filters: {id: 2}) {
      id
      name
    }
  }
  teacher2: teachers {
    id
    name
    courses(filters: {id: 1}) {
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
                    "courses": [{"id": 2, "name": "Physics"}],
                },
            ],
            "teacher2": [
                {
                    "id": 1,
                    "name": "Some Teacher",
                    "courses": [{"id": 1, "name": "Mathematics"}],
                },
            ],
        },
    }


def test_multi_query_one(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
  courses {
    teacher(filters: {id: 1}) {
      name
    }
    name
  }
  courses2: courses {
    teacher(filters: {id: 2}) {
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
            "courses": [
                {"teacher": {"name": "Some Teacher"}, "name": "Mathematics"},
                {"teacher": {"name": "Some Teacher"}, "name": "Physics"},
            ],
            "courses2": [
                {"teacher": None, "name": "Mathematics"},
                {"teacher": None, "name": "Physics"},
            ],
        },
    }


def test_multi_key(client_data):
    response = client_data.post(
        "/graphql",
        json={
            "query": """query MyQuery {
  students {
    name
    birthDate
    courses {
      course {
        name
      }
      grader {
        semester
        grade
      }
    }
  }
}""",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "students": [
                {
                    "name": "Some Name",
                    "birthDate": "1999-09-16",
                    "courses": [
                        {
                            "course": {"name": "Mathematics"},
                            "grader": [{"semester": 1, "grade": 10.0}],
                        },
                        {
                            "course": {"name": "Physics"},
                            "grader": [{"semester": 1, "grade": 9.0}],
                        },
                    ],
                },
                {
                    "name": "Other Name",
                    "birthDate": "1999-07-24",
                    "courses": [
                        {
                            "course": {"name": "Mathematics"},
                            "grader": [{"semester": 1, "grade": 8.0}],
                        },
                        {"course": {"name": "Physics"}, "grader": []},
                    ],
                },
                {
                    "name": "Another Name",
                    "birthDate": "1998-05-12",
                    "courses": [
                        {"course": {"name": "Mathematics"}, "grader": []},
                    ],
                },
            ],
        },
    }
