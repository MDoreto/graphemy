def test_auto_foreign_key():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlmodel import Session, create_engine
    from sqlmodel.pool import StaticPool

    from graphemy import Dl, Field, Graphemy, GraphemyRouter, Setup

    class Base(Graphemy, table=True):
        id: int | None = Field(primary_key=True, default=None)
        fk_1: str
        fk_2: str
        center_id: str | None
        extra: 'Extra' = Dl(source=['fk_1', 'fk_2'], target=['fk_1', 'fk_2'])
        center: 'Center' = Dl(
            source='center_id', target='id', foreign_key=False
        )

    class Extra(Graphemy, table=True):
        fk_1: str = Field(primary_key=True)
        fk_2: str = Field(primary_key=True)
        base: list['Base'] = Dl(
            source=['fk_1', 'fk_2'], target=['fk_1', 'fk_2']
        )

    class Center(Graphemy, table=True):
        id: str = Field(primary_key=True)
        name: str
        base: list['Base'] = Dl(source='id', target='center_id')

    engine = create_engine(
        'sqlite://',
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
    )
    Graphemy.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Center(name='Center 1', id='1'))
        session.add(Extra(fk_1='1', fk_2='1'))
        session.add(Extra(fk_1='2', fk_2='1'))
        session.add(Base(fk_1='1', fk_2='1', center_id='1'))
        session.add(Base(fk_1='2', fk_2='1', center_id=None))
        session.commit()

    app = FastAPI()
    router = GraphemyRouter(engine={'default': engine}, auto_foreign_keys=True)
    app.include_router(router, prefix='/graphql')
    client = TestClient(app)
    response = client.post(
        '/graphql',
        json={
            'query': """query MyQuery {
                            bases {
                                fk1
                                fk2
                                center {
                                    name
                                }
                                extra {
                                    fk1
                                    fk2
                                }
                            
                        }}"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'bases': [
                {
                    'fk1': '1',
                    'fk2': '1',
                    'center': {'name': 'Center 1'},
                    'extra': {'fk1': '1', 'fk2': '1'},
                },
                {
                    'fk1': '2',
                    'fk2': '1',
                    'center': None,
                    'extra': {'fk1': '2', 'fk2': '1'},
                },
            ]
        }
    }


def test_strawberry_class():
    import strawberry
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlmodel import Session, create_engine
    from sqlmodel.pool import StaticPool

    from graphemy import Dl, Field, Graphemy, GraphemyRouter, Setup

    class User(Graphemy, table=True):
        id: int | None = Field(primary_key=True, default=None)
        first_name: str
        last_name: str

        class Strawberry:
            @strawberry.field
            async def full_name(self) -> str:
                return f'{self.first_name} {self.last_name}'

    engine = create_engine(
        'sqlite://',
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
    )
    Graphemy.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(User(first_name='John', last_name='Doe'))
        session.commit()

    app = FastAPI()
    router = GraphemyRouter(engine=engine, auto_foreign_keys=True)
    app.include_router(router, prefix='/graphql')
    client = TestClient(app)
    response = client.post(
        '/graphql',
        json={
            'query': """query MyQuery {
                            users {
                                firstName
                                lastName
                                fullName
                            }
                            
                        }"""
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'users': [
                {
                    'firstName': 'John',
                    'lastName': 'Doe',
                    'fullName': 'John Doe',
                },
            ]
        }
    }
