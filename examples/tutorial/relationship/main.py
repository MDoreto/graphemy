from datetime import date

from fastapi import FastAPI
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from examples.tutorial.relationship.models import (
    Course,
    Grade,
    Student,
    StudentCourse,
    Teacher,
    School
)
from graphemy import Graphemy, GraphemyRouter

engine = create_engine(
    "sqlite://",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
Graphemy.metadata.create_all(engine)

with Session(engine) as session:
    session.add(School(name="Some School"))
    session.add(Teacher(name="Some Teacher", school_id=1))
    session.add(Course(name="Mathematics", teacher_id=1))
    session.add(Course(name="Physics", teacher_id=1))
    session.add(Student(name="Some Name", birth_date=date(1999, 9, 16), school_id=1))
    session.add(Student(name="Other Name", birth_date=date(1999, 7, 24), school_id=1))
    session.add(Student(name="Another Name", birth_date=date(1998, 5, 12), school_id=1))
    session.add(StudentCourse(student_id=1, course_id=1))
    session.add(StudentCourse(student_id=1, course_id=2))
    session.add(StudentCourse(student_id=2, course_id=1))
    session.add(StudentCourse(student_id=2, course_id=2))
    session.add(StudentCourse(student_id=3, course_id=1))
    session.add(Grade(student_id=1, course_id=1, grade=10.0, semester=1))
    session.add(Grade(student_id=1, course_id=2, grade=9.0, semester=1))
    session.add(Grade(student_id=2, course_id=1, grade=8.0, semester=1))
    session.commit()

app = FastAPI()
router = GraphemyRouter(
    engine=engine,
    enable_put_mutations=True,
    enable_delete_mutations=True,
)
app.include_router(router, prefix="/graphql")
