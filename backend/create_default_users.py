import os
import django
from datetime import date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from apps.Users.models import (
    Program, Section, StudentProfile,
    StaffProfile, FacultyProfile, FacultyDepartment, Position,
)

User = get_user_model()


def get_user(identifier):
    if isinstance(identifier, int):
        return User.objects.filter(pk=identifier).first()
    if "@" in identifier:
        return User.objects.filter(email__iexact=identifier).first()
    return User.objects.filter(username__iexact=identifier).first()


def assign_role(identifier, new_role):
    u = User.objects.get(username=identifier)
    u.groups.remove(Group.objects.get(name="student"))
    u.groups.add(Group.objects.get(name=new_role))


def create_users():
    print("\n" + "="*60)
    print("CREATING DEFAULT USERS")
    print("="*60 + "\n")

    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@cmu.edu.ph",
            password="admin123",
            institutional_id="ADM-0001",
            role_type="admin",
        )
        assign_role("admin", "admin")
        print("Admin superuser created")
    else:
        print("Admin already exists")

    if not User.objects.filter(username="Marcus").exists():
        user1 = User.objects.create_user(
            username="Marcus",
            email="immarcusmercer@gmail.com",
            password="password123",
            first_name="Marcus",
            last_name="Mercer",
            institutional_id="456456456",
            role_type="student",
        )
        assign_role("Marcus", "student")

        prog, _ = Program.objects.get_or_create(program_name="BS IT")
        sec, _ = Section.objects.get_or_create(section_name="IT-1A")
        StudentProfile.objects.create(
            user=user1,
            program=prog,
            section=sec,
            year_level=1,
            indiv_points=0,
        )
        print(f"Account {user1.get_username()} created")
    else:
        print("Marcus already exists.")

    pos1, _ = Position.objects.get_or_create(position_name="Instructor 1")
    dep1, _ = FacultyDepartment.objects.get_or_create(department_name="CISC")

    if not User.objects.filter(username="Donald").exists():
        user2 = User.objects.create_user(
            username="Donald",
            email="donaldtrump@cmu.edu.ph",
            password="password123",
            first_name="Donald",
            last_name="Trump",
            institutional_id="123123123",
            role_type="staff",
        )
        assign_role("Donald", "staff")
        StaffProfile.objects.create(
            user=user2,
            faculty_department=dep1,
            job_title="registrar",
        )
        print(f"Account {user2.get_username()} created")
    else:
        print("Donald already exists.")

    if not User.objects.filter(username="Kim").exists():
        user3 = User.objects.create_user(
            username="Kim",
            email="kimjongun@cmu.edu.ph",
            password="password123",
            first_name="Kim",
            last_name="Jong Un",
            institutional_id="789789789",
            role_type="faculty",
        )
        assign_role("Kim", "faculty")
        FacultyProfile.objects.create(
            user=user3,
            faculty_department=dep1,
            position=pos1,
            hire_date=date(2001, 9, 11),
        )
        print(f"Account {user3.get_username()} created")
    else:
        print("Kim already exists.")

    for ident in ("admin", "Marcus", "Donald", "Kim"):
        u = get_user(ident)
        if u:
            print(f"Verified: {u.get_username()} (ID: {u.id})")
        else:
            print(f"User {ident} not found")


if __name__ == "__main__":
    create_users()
