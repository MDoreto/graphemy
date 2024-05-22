import asyncio

import pytest
import pytest_asyncio

from graphemy import Setup


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from examples.tutorial.main import app, engine

    Setup.engine = {'default': engine}

    return TestClient(app)


@pytest.fixture()
def client_data():
    from datetime import date

    from fastapi.testclient import TestClient
    from sqlmodel import Session, create_engine
    from sqlmodel.pool import StaticPool

    from examples.tutorial.main import app
    from examples.tutorial.models import (
        Course,
        Grade,
        Student,
        StudentCourse,
        Teacher,
    )
    from graphemy import Graphemy

    engine = create_engine(
        'sqlite://',
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
    )
    Graphemy.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Teacher(name='Some Teacher'))
        session.add(Course(name='Mathematics', teacher_id=1))
        session.add(Course(name='Physics', teacher_id=1))
        session.add(Student(name='Some Name', birth_date=date(1999, 9, 16)))
        session.add(Student(name='Other Name', birth_date=date(1999, 7, 24)))
        session.add(Student(name='Another Name', birth_date=date(1998, 5, 12)))
        session.add(StudentCourse(student_id=1, course_id=1))
        session.add(StudentCourse(student_id=1, course_id=2))
        session.add(StudentCourse(student_id=2, course_id=1))
        session.add(StudentCourse(student_id=2, course_id=2))
        session.add(StudentCourse(student_id=3, course_id=1))
        session.add(Grade(student_id=1, course_id=1, grade=10.0, semester=1))
        session.add(Grade(student_id=1, course_id=2, grade=9.0, semester=1))
        session.add(Grade(student_id=2, course_id=1, grade=8.0, semester=1))
        session.commit()
    Setup.engine = {'default': engine}

    return TestClient(app)


@pytest_asyncio.fixture(scope='module')
async def client_async():
    from fastapi import FastAPI
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlmodel.main import default_registry

    from graphemy import Field, Graphemy, GraphemyRouter, Setup

    app = FastAPI()

    engine = create_async_engine(
        'sqlite+aiosqlite:///',
        connect_args={'check_same_thread': False},
    )

    class User(Graphemy, table=True):
        __enable_put_mutation__ = True
        __enable_delete_mutation__ = True
        id: int | None = Field(primary_key=True, default=None)
        name: str
        qtd: int

    async with engine.begin() as conn:
        await conn.run_sync(Graphemy.metadata.create_all)

    router = GraphemyRouter(engine=engine)
    app.include_router(router, prefix='/graphql')
    async with AsyncClient(app=app, base_url='http://test') as ac:
        yield ac
    Setup.classes = {}
    Setup.async_engine = False
    Graphemy.metadata.clear()
    default_registry.dispose()


@pytest.fixture(scope='module')
def client_auth():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlmodel import Session, create_engine
    from sqlmodel.pool import StaticPool

    from graphemy import Dl, Field, Graphemy, GraphemyRouter, Setup

    class Resource(Graphemy, table=True):
        id: int | None = Field(primary_key=True, default=None)
        name: str
        category: str
        owner_id: str | None
        private_id: int | None
        owner: 'Owner' = Dl(source='owner_id', target='id')
        private: 'Private' = Dl(source='private_id', target='id')

    class Owner(Graphemy, table=True):
        id: str | None = Field(primary_key=True, default=None)
        name: str
        resources: list['Resource'] = Dl(source='id', target='owner_id')
        privates: list['Private'] = Dl(source='id', target='owner_id')
        keys: list['Key'] = Dl(source='id', target='owner_id')

    class Private(Graphemy, table=True):
        id: int | None = Field(primary_key=True, default=None)
        description: str
        owner_id: str
        owner: 'Owner' = Dl(source='owner_id', target='id')

    class Key(Graphemy, table=True):
        id: int | None = Field(primary_key=True, default=None)
        description: str
        owner_id: str
        owner: 'Owner' = Dl(source='owner_id', target='id')

    engine = create_engine(
        'sqlite://',
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
    )
    Graphemy.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Owner(id='1', name='Center 1'))
        session.add(
            Resource(
                id=1, name='Base 1', category='A', owner_id='1', private_id=1
            )
        )
        session.add(
            Resource(
                id=2, name='Base 2', category='B', owner_id='1', private_id=1
            )
        )
        session.add(
            Resource(
                id=3,
                name='Base 3',
                category='C',
                owner_id='2',
                private_id=None,
            )
        )
        session.add(Private(id=1, description='Extra 1', owner_id='1'))
        session.commit()

    async def get_context(request, response):
        user = {'categories': ['A', 'B'], 'classes': ['Resource', 'Owner']}
        request.scope['user'] = user
        return {'user': user}

    def dl_filter(data, request):
        user = request.scope['user']
        if (
            data
            and isinstance(data, list)
            and len(data) > 0
            and isinstance(data[0], Resource)
        ):
            return [d for d in data if d.category in user['categories']]
        return data

    def query_filter(model, info):
        if model.__name__ == 'Resource':
            return model.category.in_(info.context['user']['categories'])
        return True

    async def permission_getter(module_class, context, request_type):
        return module_class.__name__ in context['user']['classes']

    app = FastAPI()
    router = GraphemyRouter(
        engine=engine,
        dl_filter=dl_filter,
        query_filter=query_filter,
        permission_getter=permission_getter,
        context_getter=get_context,
    )
    app.include_router(router, prefix='/graphql')
    return TestClient(app)
