import os
import django
from datetime import date
import random

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from apps.Users.models import Program, Section as UserSection, StudentProfile, FacultyProfile, FacultyDepartment, Position
from apps.Academics.models import Semester, Curriculum, Course, Section as AcademicSection, Class, Enrollment
from apps.Progress.models import FinalGrade, FacultyFeedbackMessage

User = get_user_model()


# ---------------------------------------------------------------
# GROUPS
# ---------------------------------------------------------------
def create_groups():
    for role in ("admin", "faculty", "staff", "student"):
        Group.objects.get_or_create(name=role)
    print("✓ Groups created")


# ---------------------------------------------------------------
# USERS
# ---------------------------------------------------------------
def create_users():
    admin, created = User.objects.get_or_create(
        username="admin",
        defaults=dict(
            email="admin@cmu.edu.ph",
            institutional_id="ADM0001",
            role_type="admin",
            is_superuser=True,
            is_staff=True
        )
    )
    if created:
        admin.set_password("admin123")
        admin.save()
    admin.groups.add(Group.objects.get(name="admin"))

    faculty_info = [
        ("profA", "Albert", "Einstein"),
        ("profB", "Ada", "Lovelace"),
        ("profC", "Linus", "Torvalds"),
    ]
    faculties = []
    for uname, fn, ln in faculty_info:
        user, _ = User.objects.get_or_create(
            username=uname,
            defaults=dict(
                email=f"{uname}@cmu.edu.ph",
                institutional_id=uname.upper(),
                role_type="faculty",
                first_name=fn,
                last_name=ln
            )
        )
        user.set_password("password123")
        user.save()
        user.groups.add(Group.objects.get(name="faculty"))
        faculties.append(user)

    student_info = [
        ("stud1", "John", "Wick"),
        ("stud2", "Sarah", "Connor"),
        ("stud3", "Arthur", "Morgan"),
        ("stud4", "Eren", "Yeager"),
        ("stud5", "Naruto", "Uzumaki"),
        ("stud6", "Mikasa", "Ackerman"),
        ("stud7", "Vegeta", "Saiyan"),
        ("stud8", "Tony", "Stark"),
    ]
    students = []
    for uname, fn, ln in student_info:
        user, _ = User.objects.get_or_create(
            username=uname,
            defaults=dict(
                email=f"{uname}@cmu.edu.ph",
                institutional_id=uname.upper(),
                role_type="student",
                first_name=fn,
                last_name=ln
            )
        )
        user.set_password("password123")
        user.save()
        user.groups.add(Group.objects.get(name="student"))
        students.append(user)

    print("✓ Users created")
    return faculties, students


# ---------------------------------------------------------------
# PROFILES
# ---------------------------------------------------------------
def create_profiles(faculties, students):
    program, _ = Program.objects.get_or_create(
        program_name="BS Information Technology",
        defaults=dict(abbr="BSIT")
    )

    sectionA, _ = UserSection.objects.get_or_create(section_name="IT-1A")
    sectionB, _ = UserSection.objects.get_or_create(section_name="IT-1B")

    dep, _ = FacultyDepartment.objects.get_or_create(department_name="CISC")
    pos, _ = Position.objects.get_or_create(position_name="Instructor 1")

    faculty_profiles = []
    for fac in faculties:
        p, _ = FacultyProfile.objects.get_or_create(
            user=fac,
            defaults=dict(faculty_department=dep, position=pos, hire_date=date(2020, 6, 1))
        )
        faculty_profiles.append(p)

    student_profiles = []
    for i, stu in enumerate(students):
        target = sectionA if i < 4 else sectionB
        sp, _ = StudentProfile.objects.get_or_create(
            user=stu,
            defaults=dict(program=program, section=target, year_level=1)
        )
        student_profiles.append(sp)

    print("✓ Profiles created")
    return program, student_profiles, faculty_profiles


# ---------------------------------------------------------------
# ACADEMICS
# ---------------------------------------------------------------
def seed_academics(program, student_profiles, faculty_profiles):
    sem1, _ = Semester.objects.get_or_create(
        academic_year="2024-2025", term="first",
        start_date=date(2024, 8, 1), end_date=date(2024, 12, 15), defaults=dict(is_active=True)
    )
    sem2, _ = Semester.objects.get_or_create(
        academic_year="2024-2025", term="second",
        start_date=date(2025, 1, 10), end_date=date(2025, 5, 20), defaults=dict(is_active=False)
    )

    curriculum, _ = Curriculum.objects.get_or_create(
        program=program, revision_year=2024, defaults=dict(is_active=True)
    )

    courses = [
        ("IT101", "Introduction to Computing", 3),
        ("IT102", "Computer Programming 1", 3),
        ("IT103", "Discrete Mathematics", 3),
        ("IT104", "Digital Logic", 2),
    ]

    course_objs = []
    for c, title, units in courses:
        cc, _ = Course.objects.get_or_create(
            code=c,
            defaults=dict(title=title, units=units, lec_hours=units, lab_hours=0,
                          curriculum=curriculum, year_offered="1", term_offered="first")
        )
        course_objs.append(cc)

    classes = []
    for sem in (sem1, sem2):
        sectionA, _ = AcademicSection.objects.get_or_create(name="A", curriculum=curriculum, semester=sem, year="1", type="lec", defaults=dict(capacity=50))
        sectionB, _ = AcademicSection.objects.get_or_create(name="B", curriculum=curriculum, semester=sem, year="1", type="lec", defaults=dict(capacity=50))

        for i, course in enumerate(course_objs):
            fac = faculty_profiles[i % len(faculty_profiles)]
            sec = sectionA if i < 2 else sectionB
            cls, created = Class.objects.get_or_create(course=course, section=sec, semester=sem)
            if created:
                cls.faculty = fac
                cls.save()
            classes.append(cls)

        for sp in student_profiles:
            for cls in classes:
                if cls.section.name == sp.section.section_name[-1] and cls.semester == sem:
                    Enrollment.objects.get_or_create(enrolled_class=cls, student=sp)

    print("✓ Academics seeded")
    return classes


# ---------------------------------------------------------------
# PROGRESS
# ---------------------------------------------------------------
def seed_progress(student_profiles, classes):
    for sp in student_profiles:
        for cls in classes:
            if cls.section.name == sp.section.section_name[-1]:
                failed = random.choice([True, False])

                fg, _ = FinalGrade.objects.get_or_create(
                    student=sp.user,
                    course=cls.course,
                    semester=cls.semester,
                    defaults=dict(
                        midterm_grade="2.50" if failed else "2.25",
                        final_term_grade="3.00" if failed else "1.75",
                        final_grade="3.00" if failed else "2.00",
                        status="failed" if failed else "passed",
                        re_exam="3.00" if failed else ""
                    )
                )

                for _ in range(random.randint(1, 2)):
                    FacultyFeedbackMessage.objects.get_or_create(
                        student=sp.user,
                        faculty=cls.faculty.user,
                        grade=fg,
                        defaults=dict(
                            message=random.choice([
                                "Good effort!",
                                "Improve attendance.",
                                "Struggling with quizzes.",
                                "Strong performance!",
                                "Maintain consistency."
                            ])
                        )
                    )

    print("✓ Progress seeded")


# ---------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------
if __name__ == "__main__":
    print("\n⏳ Seeding database...")
    create_groups()
    faculties, students = create_users()
    program, student_profiles, faculty_profiles = create_profiles(faculties, students)
    classes = seed_academics(program, student_profiles, faculty_profiles)
    seed_progress(student_profiles, classes)
    print("\n🎉 DATABASE SEEDED SUCCESSFULLY!")
