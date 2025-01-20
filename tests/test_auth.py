def test_class_permission(client_auth):
    response = client_auth.post(
        "/graphql",
        json={
            "query": """query MyQuery {
                privates {
                    id
                    description
                }
            }""",
        },
    )
    assert response.status_code == 403
    assert response.json() == {
        "data": {"privates": []},
        "errors": [
            {
                "message": "User doesn't have necessary permissions for this path",
                "path": ["private"],
            },
        ],
    }


def test_permission_dl(client_auth):
    response = client_auth.post(
        "/graphql",
        json={
            "query": """query MyQuery {
                owners {
                    id
                    name
                    privates {
                        id
                        description
                    }
                    keys{
                        id
                        description
                    }
                }
            }""",
        },
    )
    assert response.status_code == 403
    assert response.json() == {
        "data": {
            "owners": [
                {"id": "1", "name": "Center 1", "privates": [], "keys": []},
            ],
        },
        "errors": [
            {
                "message": "User doesn't have necessary permissions for this path",
                "path": ["private", "key"],
            },
        ],
    }


def test_permission_dl_one(client_auth):
    response = client_auth.post(
        "/graphql",
        json={
            "query": """query MyQuery {
                resources {
                    id
                    name
                    private {
                        id
                        description
                    }
                }
            }""",
        },
    )
    assert response.status_code == 403
    assert response.json() == {
        "data": {
            "resources": [
                {"id": 1, "name": "Base 1", "private": None},
                {"id": 2, "name": "Base 2", "private": None},
            ],
        },
        "errors": [
            {
                "message": "User doesn't have necessary permissions for this path",
                "path": ["private"],
            },
        ],
    }


def test_query_permission(client_auth):
    response = client_auth.post(
        "/graphql",
        json={
            "query": """query MyQuery {
                resources {
                    id
                    name
                    category
                }
            }""",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "resources": [
                {"category": "A", "id": 1, "name": "Base 1"},
                {"category": "B", "id": 2, "name": "Base 2"},
            ],
        },
    }


def test_dl_filter(client_auth):
    response = client_auth.post(
        "/graphql",
        json={
            "query": """query MyQuery {
                owners {
                    id
                    name
                    resources{
                        id
                        category
                    }
                }
            }""",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "owners": [
                {
                    "id": "1",
                    "name": "Center 1",
                    "resources": [
                        {"id": 1, "category": "A"},
                        {"id": 2, "category": "B"},
                    ],
                },
            ],
        },
    }
