from datetime import date

from graphemy import Dl, Field, Graphemy


class Teacher(Graphemy, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str
    courses: list["Course"] = Dl(source="id", target="teacher_id")
    school_id: int
    school: "School" = Dl(source="school_id", target="id")


class Course(Graphemy, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str
    students: list["StudentCourse"] = Dl(source="id", target="course_id")
    teacher_id: int
    teacher: "Teacher" = Dl(source="teacher_id", target="id")


class Student(Graphemy, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str | None
    birth_date: date
    courses: list["StudentCourse"] = Dl(source="id", target="student_id")
    school_id: int
    school: "School" = Dl(source="school_id", target="id")


class StudentCourse(Graphemy, table=True):
    student_id: int = Field(primary_key=True)
    course_id: int = Field(primary_key=True)
    student: "Student" = Dl(source="student_id", target="id")
    course: "Course" = Dl(source="course_id", target="id")
    grader: list["Grade"] = Dl(
        source=["student_id", "course_id"],
        target=["student_id", "course_id"],
    )


class Grade(Graphemy, table=True):
    student_id: int = Field(primary_key=True)
    course_id: int = Field(primary_key=True)
    grade: float
    semester: int = Field(primary_key=True)
    student_course: "StudentCourse" = Dl(
        source=["student_id", "course_id"],
        target=["student_id", "course_id"],
    )


class School(Graphemy, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str
    students: list["Student"] = Dl(source="id", target="school_id")
    teachers: list["Teacher"] = Dl(source="id", target="school_id")
