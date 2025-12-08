import os
import django
import sys
#
# sys.path.insert(0, r'C:\dev\vhub\finals\master-route-navigation')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

django.setup()

from datetime import date
from apps.Academics.models import *
from apps.Users.models import Program

sem1 = Semester.objects.create(
        term="first",
        start_date=date(2025, 6, 1),
        end_date=date(2025, 10, 31),
        academic_year="2025-2026",
        is_active=False
    )

sem2 = Semester.objects.create(
        term="second",
        start_date=date(2025, 11, 1),
        end_date=date(2026, 3, 31),
        academic_year="2025-2026",
        is_active=True
    )

program1 = Program.objects.create(program_name="BS Information Technology", abbr="BSIT")
program2 = Program.objects.create(program_name="BS Computer Science", abbr="BSCS")

curriculum1 = Curriculum.objects.create(
    program=program1,
    revision_year=2025,
    is_active=True
)
curriculum2 = Curriculum.objects.create(
    program=program2,
    revision_year=2025,
    is_active=True
)

# BSIT Sections
section1 = Section.objects.create(
        name="A",
        curriculum=curriculum1,
        semester=sem2,
        year="1",
        type="lec",
        capacity=40
    )

section2 = Section.objects.create(
        name="B",
        curriculum=curriculum1,
        semester=sem2,
        year="2",
        type="lec",
        capacity=40
    )

section3 = Section.objects.create(
        name="C",
        curriculum=curriculum1,
        semester=sem2,
        year="3",
        type="lec",
        capacity=40
    )

section4 = Section.objects.create(
        name="D",
        curriculum=curriculum1,
        semester=sem2,
        year="4",
        type="lec",
        capacity=40
    )

# BSCS sections
section5 = Section.objects.create(
        name="A",
        curriculum=curriculum2,
        semester=sem2,
        year="1",
        type="lec",
        capacity=40
    )

section6 = Section.objects.create(
        name="B",
        curriculum=curriculum2,
        semester=sem2,
        year="2",
        type="lec",
        capacity=40
    )

section7 = Section.objects.create(
        name="C",
        curriculum=curriculum2,
        semester=sem2,
        year="3",
        type="lec",
        capacity=40
    )

section8 = Section.objects.create(
        name="D",
        curriculum=curriculum2,
        semester=sem2,
        year="4",
        type="lec",
        capacity=40
    )
