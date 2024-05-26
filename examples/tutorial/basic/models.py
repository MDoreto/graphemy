from datetime import date

from graphemy import Field, Graphemy


class Student(Graphemy, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str
    birth_date: date


class StudentCourse(Graphemy, table=True):
    student_id: int = Field(primary_key=True)
    course_id: int = Field(primary_key=True)


class Course(Graphemy, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str
