# Script for creating a test account

from django.contrib.auth import get_user_model
from apps.Users.models import Program, Section, StudentProfile, Organization, OrgMembership

User = get_user_model()

# 1) Create the base user (your BaseUser)
u = User.objects.create_user(
    username="test456",
    email="test456@cmu.edu.ph",
    password="password123",
    first_name="Johnny",
    last_name="Sinns",
    institutional_id="2025000002",
    role_type="student",
)

# 2) Create student profile
prog = Program.objects.get_or_create(program_name="BS Information Management")[0]
sec  = Section.objects.get_or_create(section_name="IM-1A")[0]

sp = StudentProfile.objects.create(
    user=u,
    program=prog,
    section=sec,
    year_level=1,
    indiv_points=0,
)

# 3) Create an organization and make this student an officer
org = Organization.objects.get_or_create(name="Science Club")[0]

OrgMembership.objects.create(
    student=sp,
    organization=org,
    role="pres",       # or "officer", "sec", "treas", etc.
    is_active=True,
)

print("Done. Try logging in with username 's01' / password 'testpass123'.")
