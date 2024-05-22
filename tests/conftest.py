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
