import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# 1) Absolute path to the project root (folder that contains the config package)
PROJECT_ROOT = r"D:\master-route-navigation\backend"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 2) Point DJANGO_SETTINGS_MODULE to your real settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

print("sys.path[0]:", sys.path[0])
print("DJANGO_SETTINGS_MODULE:", os.environ["DJANGO_SETTINGS_MODULE"])

django.setup()

from django.contrib.contenttypes.models import ContentType
from apps.Users.models import BaseUser
from apps.Announcements.models import Announcements, AuthUser
from apps.Calendar.models import CalendarEntry, CalendarLogs, Holiday


def create_mock_users():
    admin, _ = BaseUser.objects.get_or_create(
        username="calendar_admin",
        defaults={
            "email": "calendar_admin@example.com",
            "first_name": "Calendar",
            "last_name": "Admin",
            "institutional_id": "CAL-0001",
            "role_type": "admin",
        },
    )
    return admin


def create_mock_announcement(author: BaseUser):
    # Optional: try to match an AuthUser by username; may be None
    auth_author = AuthUser.objects.filter(username=author.username).first()

    ann, _ = Announcements.objects.get_or_create(
        title="Mock Org General Assembly",
        defaults={
            "body": "Sample announcement for testing calendar integration.",
            "author": auth_author,  # can be None; field is nullable
        },
    )
    return ann


def parse_event_datetime(dt_str):
    date_part, time_part = dt_str.split("\n")
    return datetime.strptime(f"{date_part} {time_part}", "%m/%d/%Y %I:%M %p")


def add_event(event_data, admin):
    dt = parse_event_datetime(event_data["date_time"])
    dt = timezone.make_aware(dt)  # see timezone section below

    event_type = event_data["type"]
    title = event_data["event"]
    location = event_data["location"]

    ct = ContentType.objects.get_for_model(Announcements)

    entry, _ = CalendarEntry.objects.update_or_create(
        source_ct=ct,
        source_id=0,  # conventional dummy id for imported events
        start_at=dt,
        end_at=dt + timedelta(hours=2),
        defaults={
            "title": title,
            "all_day": False,
            "location": location,
            "is_public": True,
            "tags": [event_type.lower(), "imported"],
            "org_status": "",
            "org_id": None,
            "section_id": None,
            "semester_id": None,
        },
    )

    CalendarLogs.objects.create(
        event=entry,
        action=f"imported {event_type.lower()} event",
        performed_by=admin,
        details=f"Imported event '{title}' of type {event_type}.",
    )


def create_mock_calendar_data():
    admin = create_mock_users()
    ann = create_mock_announcement(admin)

    # Original announcement entry
    now = datetime.now()
    start = now + timedelta(days=1, hours=9)
    end = start + timedelta(hours=2)

    ct = ContentType.objects.get_for_model(Announcements)
    entry, _ = CalendarEntry.objects.update_or_create(
        source_ct=ct,
        source_id=ann.pk,
        defaults={
            "title": ann.title,
            "start_at": start,
            "end_at": end,
            "all_day": False,
            "location": ann.location or "CISC Auditorium",
            "is_public": True,
            "tags": ["announcement", "test"],
            "org_status": "",
            "org_id": None,
            "section_id": None,
            "semester_id": None,
        },
    )

    CalendarLogs.objects.create(
        event=entry,
        action="created",
        performed_by=admin,
        details="Mock entry created for testing.",
    )

    Holiday.objects.get_or_create(
        name="Mock Foundation Day",
        date=(now + timedelta(days=7)).date(),
        defaults={
            "description": "Sample holiday for calendar testing.",
            "created_by": admin,
        },
    )

    events_data = [
    {"date_time": "06/02/2025\n9:00 AM", "event": "Enrollment – First Year, First Semester", "type": "Academic", "location": "CMU", "status": "Finished"},
    {"date_time": "07/01/2025\n9:00 AM", "event": "Enrollment – Regular Continuing Students, First Semester", "type": "Academic", "location": "CMU", "status": "Finished"},
    {"date_time": "07/30/2025\n9:00 AM", "event": "Enrollment – Irregular/Transferees/Short Course, First Semester", "type": "Academic", "location": "CMU", "status": "Finished"},
    {"date_time": "07/22/2025\n9:00 AM", "event": "Deadline for Enrollment Requests, First Semester", "type": "Deadline", "location": "CMU", "status": "Finished"},
    {"date_time": "08/01/2025\n9:00 AM", "event": "Deadline for Application of Advance Credit (Admitted as of First Sem AY 2024–2025)", "type": "Deadline", "location": "CMU", "status": "Finished"},
    {"date_time": "08/04/2025\n9:00 AM", "event": "Start of Classes – First Semester", "type": "Academic", "location": "CMU", "status": "Finished"},
    {"date_time": "08/11/2025\n9:00 AM", "event": "Change in Registration – First Semester", "type": "Academic", "location": "CMU", "status": "Finished"},
    {"date_time": "09/23/2025\n9:00 AM", "event": "Midterm Examination – First Semester", "type": "Academic", "location": "CMU", "status": "Finished"},
    {"date_time": "10/10/2025\n9:00 AM", "event": "Deadline for Uploading of Midterm Grades – First Semester", "type": "Deadline", "location": "CMU", "status": "Finished"},
    {"date_time": "10/27/2025\n9:00 AM", "event": "Reading Week – First Semester", "type": "Academic", "location": "CMU", "status": "Finished"},
    {"date_time": "11/13/2025\n9:00 AM", "event": "Final Examination – First Semester", "type": "Academic", "location": "CMU", "status": "Finished"},
    {"date_time": "8/3/2025\n9:00 AM", "event": "Last Day of Thesis Defense – First Semester", "type": "Deadline", "location": "CMU", "status": "Upcoming"},
    {"date_time": "12/09/2025\n9:00 AM", "event": "Removal Examination – First Semester", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "12/12/2025\n9:00 AM", "event": "Deadline for Submission of Final Grades & Thesis – First Semester", "type": "Deadline", "location": "CMU", "status": "Upcoming"},
    {"date_time": "12/16/2025\n9:00 AM", "event": "Deadline for Submission of Grade Sheets to OUR – First Semester", "type": "Deadline", "location": "CMU", "status": "Upcoming"},
    {"date_time": "12/06/2025\n9:00 AM", "event": "End of Classes – First Semester", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "01/05/2026\n9:00 AM", "event": "Enrollment – First Year, Second Semester", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "01/22/2026\n9:00 AM", "event": "Enrollment – Regular Continuing Students, Second Semester", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "02/07/2026\n9:00 AM", "event": "Enrollment – Irregular/Transferees/Short Course, Second Semester", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "01/05/2026\n9:00 AM", "event": "Deadline for Enrollment Requests – Second Semester", "type": "Deadline", "location": "CMU", "status": "Upcoming"},
    {"date_time": "01/12/2026\n9:00 AM", "event": "Start of Classes – Second Semester", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "01/19/2026\n9:00 AM", "event": "Change in Registration – Second Semester", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "03/02/2026\n9:00 AM", "event": "Midterm Examination – Second Semester", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "03/19/2026\n9:00 AM", "event": "Deadline for Uploading of Midterm Grades – Second Semester", "type": "Deadline", "location": "CMU", "status": "Upcoming"},
    {"date_time": "03/23/2026\n9:00 AM", "event": "Reading Week – Second Semester", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "05/11/2026\n9:00 AM", "event": "Final Examination – Second Semester", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "05/13/2026\n9:00 AM", "event": "Last Day of Thesis Defense – Second Semester", "type": "Deadline", "location": "CMU", "status": "Upcoming"},
    {"date_time": "05/18/2026\n9:00 AM", "event": "Removal Examination – Second Semester", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "05/22/2026\n9:00 AM", "event": "Deadline for Submission of Final Grades & Thesis – Second Semester", "type": "Deadline", "location": "CMU", "status": "Upcoming"},
    {"date_time": "05/25/2026\n9:00 AM", "event": "End of Classes – Second Semester", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "08/04/2025\n9:00 AM", "event": "Opening Mass (AY 2025–2026)", "type": "Organizational", "location": "CMU", "status": "Finished"},
    {"date_time": "08/06/2025\n9:00 AM", "event": "College/Department Orientation and General Assembly 2025", "type": "Academic", "location": "CMU", "status": "Finished"},
    {"date_time": "08/06/2025\n9:00 AM", "event": "SSC General Assembly 2025", "type": "Organizational", "location": "CMU", "status": "Finished"},
    {"date_time": "09/14/2025\n9:00 AM", "event": "115th Founding Anniversary and Grand Alumni Homecoming", "type": "Organizational", "location": "CMU", "status": "Finished"},
    {"date_time": "10/06/2025\n9:00 AM", "event": "Faculty Conference 2025", "type": "Organizational", "location": "CMU", "status": "Finished"},
    {"date_time": "10/06/2025\n9:00 AM", "event": "CMUFAI General Assembly 2025", "type": "Organizational", "location": "CMU", "status": "Finished"},
    {"date_time": "10/06/2025\n9:00 AM", "event": "Teachers’ Day Celebration 2025", "type": "Organizational", "location": "CMU", "status": "Finished"},
    {"date_time": "10/27/2025\n9:00 AM", "event": "Annual University Operational & Strategic Planning 2025", "type": "Organizational", "location": "CMU", "status": "Finished"},
    {"date_time": "11/03/2025\n9:00 AM", "event": "2nd Internal Quality Audit 2025", "type": "Organizational", "location": "CMU", "status": "Finished"},
    {"date_time": "11/18/2025\n9:00 AM", "event": "2nd Management Review 2025", "type": "Organizational", "location": "CMU", "status": "Finished"},
    {"date_time": "11/25/2025\n9:00 AM", "event": "PDEA Drug Education Activity 2025", "type": "Organizational", "location": "CMU", "status": "Finished"},
    {"date_time": "11/28/2025\n9:00 AM", "event": "Faculty and Staff Palaro 2025", "type": "Organizational", "location": "CMU", "status": "Finished"},
    {"date_time": "12/16/2025\n9:00 AM", "event": "University Christmas Party 2025", "type": "Organizational", "location": "CMU", "status": "Upcoming"},
    {"date_time": "12/17/2025\n9:00 AM", "event": "Teachers’ Leave (Semestral Break – 22 Days)", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "01/14/2026\n9:00 AM", "event": "College/Department Orientation and General Assembly 2026", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "01/16/2026\n9:00 AM", "event": "SSC General Assembly 2026", "type": "Organizational", "location": "CMU", "status": "Upcoming"},
    {"date_time": "03/13/2026\n9:00 AM", "event": "CMUFAI General Assembly 2026", "type": "Organizational", "location": "CMU", "status": "Upcoming"},
    {"date_time": "03/23/2026\n9:00 AM", "event": "Palaro 2026", "type": "Organizational", "location": "CMU", "status": "Upcoming"},
    {"date_time": "04/18/2026\n9:00 AM", "event": "University Recognition and Awards Day 2026", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "04/20/2026\n9:00 AM", "event": "ROE Week 2026", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "03/18/2026\n9:00 AM", "event": "Pre-employment Seminar and Job Fair 2026", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "05/26/2026\n9:00 AM", "event": "Teachers’ Leave (Long Vacation – 58 Days)", "type": "Academic", "location": "CMU", "status": "Upcoming"},
    {"date_time": "06/01/2026\n9:00 AM", "event": "1st Internal Quality Audit 2026", "type": "Organizational", "location": "CMU", "status": "Upcoming"},
    {"date_time": "01/21/2025\n9:00 AM", "event": "Ninoy Aquino Day 2025", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Finished"},
    {"date_time": "08/25/2025\n9:00 AM", "event": "National Heroes Day 2025", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Finished"},
    {"date_time": "11/01/2025\n9:00 AM", "event": "All Saints’ Day 2025", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Finished"},
    {"date_time": "11/02/2025\n9:00 AM", "event": "All Souls’ Day 2025", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Finished"},
    {"date_time": "11/30/2025\n9:00 AM", "event": "Bonifacio Day 2025", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Finished"},
    {"date_time": "12/08/2025\n9:00 AM", "event": "Feast of the Immaculate Conception of Mary 2025", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Upcoming"},
    {"date_time": "12/24/2025\n9:00 AM", "event": "Christmas Eve 2025", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Upcoming"},
    {"date_time": "12/25/2025\n9:00 AM", "event": "Christmas Day 2025", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Upcoming"},
    {"date_time": "12/30/2025\n9:00 AM", "event": "Rizal Day 2025", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Upcoming"},
    {"date_time": "12/31/2025\n9:00 AM", "event": "Last Day of the Year 2025", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Upcoming"},
    {"date_time": "01/01/2026\n9:00 AM", "event": "New Year’s Day 2026", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Upcoming"},
    {"date_time": "02/17/2026\n9:00 AM", "event": "Lunar New Year’s Day 2026", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Upcoming"},
    {"date_time": "03/20/2026\n9:00 AM", "event": "Eidul-Fitr 2026", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Upcoming"},
    {"date_time": "04/04/2026\n9:00 AM", "event": "Black Saturday 2026", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Upcoming"},
    {"date_time": "04/09/2026\n9:00 AM", "event": "Araw ng Kagitingan 2026", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Upcoming"},
    {"date_time": "05/01/2026\n9:00 AM", "event": "Labor Day 2026", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Upcoming"},
    {"date_time": "05/27/2026\n9:00 AM", "event": "Eid al-Adha (Feast of Sacrifice) 2026", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Upcoming"},
    {"date_time": "06/12/2026\n9:00 AM", "event": "Independence Day 2026", "type": "Holiday", "location": "Nationwide (Philippines)", "status": "Upcoming"},
    {"date_time": "07/01/2026\n9:00 AM", "event": "Araw ng Maramag 2026", "type": "Holiday", "location": "Maramag, Bukidnon", "status": "Upcoming"}
]


    for ev in events_data:
        add_event(ev, admin)

    print(f"✅ Created announcement entry id={entry.id}, sample holiday, and imported {len(events_data)} CMU events!")


if __name__ == "__main__":
    print("Seeding calendar data...")
    create_mock_calendar_data()
    print("Done seeding.")
