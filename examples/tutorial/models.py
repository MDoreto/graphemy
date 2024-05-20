from graphemy import Graphemy, Field, Dl
from datetime import date

class Student(Graphemy, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str 
    birth_date: date 
    courses: list["StudentCourse"] = Dl(source="id", target="student_id")

class Course(Graphemy, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str 
    students: list["StudentCourse"] = Dl(source="id", target="course_id")
    teacher_id: int
    teacher:"Teacher" = Dl(source="teacher_id", target="id")

class StudentCourse(Graphemy, table=True):
    student_id: int = Field(primary_key=True)
    course_id: int = Field(primary_key=True)
    student:"Student" = Dl(source="student_id", target="id")
    course:"Course" = Dl(source="course_id", target="id")

class Teacher(Graphemy, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str 
    courses: list["Course"] = Dl(source="id", target="teacher_id")