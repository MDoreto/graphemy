def test_no_query():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from graphemy import GraphemyRouter, Setup

    Setup.classes = {}
    app = FastAPI()
    router = GraphemyRouter()
    app.include_router(router, prefix="/graphql")
    client = TestClient(app)
    response = client.post(
        "/graphql",
        json={
            "query": """query MyQuery {
                            helloWorld
                        }""",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"data": {"helloWorld": "Hello World"}}


def test_wrong_query(client):
    response = client.post(
        "/graphql",
        json={
            "query": """query MyQuery {
                fake {
                    error
                }
            }""",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": None,
        "errors": [
            {
                "message": "Cannot query field 'fake' on type 'Query'.",
                "locations": [{"line": 2, "column": 17}],
            },
        ],
    }


def test_dl_error_type():
    import pytest

    from graphemy import Dl, Field, Graphemy

    with pytest.raises(BaseException):

        class Test(Graphemy, table=True):
            id: int | None = Field(primary_key=True, default=None)
            test1: str

        class User(Graphemy, table=True):
            id: int | None = Field(primary_key=True, default=None)
            first_name: str
            last_name: str
            test: "Test" = Dl(source="test1", target=["test1"])


def test_dl_error_length():
    import pytest

    from graphemy import Dl, Field, Graphemy

    with pytest.raises(BaseException):

        class Something(Graphemy, table=True):
            id: int | None = Field(primary_key=True, default=None)
            test1: str

        class User(Graphemy, table=True):
            id: int | None = Field(primary_key=True, default=None)
            first_name: str
            last_name: str
            something: "Something" = Dl(source=["test1", "test2"], target=["test1"])


def test_composite_with_null():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlmodel import Session, create_engine
    from sqlmodel.pool import StaticPool

    from graphemy import Dl, Field, Graphemy, GraphemyRouter

    class Source(Graphemy, table=True):
        id: int | None = Field(primary_key=True, default=None)
        fk_1: str | None
        fk_2: str | None
        target: "Target" = Dl(source=["fk_1", "fk_2"], target=["fk_1", "fk_2"])

    class Target(Graphemy, table=True):
        fk_1: str = Field(primary_key=True)
        fk_2: str = Field(primary_key=True)
        source: list["Source"] = Dl(
            source=["fk_1", "fk_2"], target=["fk_1", "fk_2"],
        )

    engine = create_engine(
        "sqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Graphemy.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Target(fk_1="1", fk_2="1"))
        session.add(Source(fk_1="2", fk_2=None))
        session.commit()

    app = FastAPI()
    router = GraphemyRouter(engine=engine, auto_foreign_keys=True)
    app.include_router(router, prefix="/graphql")
    client = TestClient(app)
    response = client.post(
        "/graphql",
        json={
            "query": """query MyQuery {
                            sources {
                                fk1
                                fk2
                                target {
                                    fk1
                                    fk2
                                }
                            
                        }}""",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": {"sources": [{"fk1": "2", "fk2": None, "target": None}]},
    }