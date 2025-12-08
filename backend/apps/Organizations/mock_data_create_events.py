# events/mock_data.py
import os
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django environment


from django.contrib.auth import get_user_model
from apps.Users.models import Program, Section, StudentProfile, FacultyProfile, FacultyDepartment, Position
from apps.Academics.models import Semester
from apps.Organizations.models import EventType, EventScheduleBlock, Event, EventSchedule, EventAttendance, EventApproval


print("Cleared all existing events data")

User = get_user_model()

def create_event_types():
    """Create the two required event types"""
    types = [
        {"event_type": "Behavioral"},
        {"event_type": "Competitive"}
    ]
    
    for type_data in types:
        obj, created = EventType.objects.get_or_create(**type_data)
        if created:
            print(f"Created EventType: {obj.event_type}")
        else:
            print(f"EventType already exists: {obj.event_type}")
    
    return EventType.objects.all()

def create_schedule_blocks():
    """Create event schedule blocks"""
    blocks = [
        {"name": "Morning Session", "description": "Events scheduled in the morning (8AM-12PM)"},
        {"name": "Afternoon Session", "description": "Events scheduled in the afternoon (1PM-5PM)"},
        {"name": "Evening Session", "description": "Events scheduled in the evening (6PM-9PM)"},
        {"name": "Full Day Event", "description": "All-day events"},
        {"name": "Weekend Special", "description": "Weekend events and activities"},
    ]
    
    created_blocks = []
    for block_data in blocks:
        obj, created = EventScheduleBlock.objects.get_or_create(**block_data)
        if created:
            print(f"Created Schedule Block: {obj.name}")
        created_blocks.append(obj)
    
    return created_blocks

def create_test_users_and_profiles():
    """Create test users with different roles"""
    
    # Get or create departments and positions
    cs_dept, _ = FacultyDepartment.objects.get_or_create(department_name="Computer Science")
    it_dept, _ = FacultyDepartment.objects.get_or_create(department_name="Information Technology")
    
    prof_pos, _ = Position.objects.get_or_create(position_name="Professor")
    asst_prof_pos, _ = Position.objects.get_or_create(position_name="Assistant Professor")
    
    # Programs and sections
    bsit_program, _ = Program.objects.get_or_create(
        program_name="BS Information Technology", 
        abbr="BSIT"
    )
    bscs_program, _ = Program.objects.get_or_create(
        program_name="BS Computer Science", 
        abbr="BSCS"
    )
    
    section_a, _ = Section.objects.get_or_create(section_name="IT-3A")
    section_b, _ = Section.objects.get_or_create(section_name="CS-3B")
    
    users_data = [
        # Org Officers (students with org_officer role)
        {
            "username": "org_officer1",
            "email": "officer1@cmu.edu.ph",
            "password": "password123",
            "first_name": "Maria",
            "last_name": "Santos",
            "institutional_id": "20240001",
            "role_type": "student",
            "profile_type": "student",
            "student_data": {
                "program": bsit_program,
                "section": section_a,
                "year_level": 3,
            },
            "groups": ["org_officer"]
        },
        {
            "username": "org_officer2", 
            "email": "officer2@cmu.edu.ph",
            "password": "password123",
            "first_name": "Juan",
            "last_name": "Cruz",
            "institutional_id": "20240002",
            "role_type": "student", 
            "profile_type": "student",
            "student_data": {
                "program": bscs_program,
                "section": section_b,
                "year_level": 2,
            },
            "groups": ["org_officer"]
        },
        
        # Regular Students
        {
            "username": "student1",
            "email": "student1@cmu.edu.ph", 
            "password": "password123",
            "first_name": "Ana",
            "last_name": "Reyes",
            "institutional_id": "20240003",
            "role_type": "student",
            "profile_type": "student",
            "student_data": {
                "program": bsit_program,
                "section": section_a,
                "year_level": 1,
            },
            "groups": []
        },
        {
            "username": "student2",
            "email": "student2@cmu.edu.ph",
            "password": "password123", 
            "first_name": "Pedro",
            "last_name": "Gonzales",
            "institutional_id": "20240004",
            "role_type": "student",
            "profile_type": "student",
            "student_data": {
                "program": bscs_program,
                "section": section_b,
                "year_level": 2,
            },
            "groups": []
        },
        
        # Faculty (approvers)
        {
            "username": "faculty1",
            "email": "faculty1@cmu.edu.ph",
            "password": "password123",
            "first_name": "Dr. Robert",
            "last_name": "Lim",
            "institutional_id": "FAC001",
            "role_type": "faculty", 
            "profile_type": "faculty",
            "faculty_data": {
                "department": cs_dept,
                "position": prof_pos,
                "hire_date": timezone.now().date() - timedelta(days=365*2)
            },
            "groups": []
        },
        {
            "username": "faculty2",
            "email": "faculty2@cmu.edu.ph",
            "password": "password123",
            "first_name": "Dr. Susan",
            "last_name": "Tan",
            "institutional_id": "FAC002",
            "role_type": "faculty",
            "profile_type": "faculty", 
            "faculty_data": {
                "department": it_dept,
                "position": asst_prof_pos,
                "hire_date": timezone.now().date() - timedelta(days=365*3)
            },
            "groups": []
        }
    ]
    
    created_users = {}
    
    for user_data in users_data:
        # Copy data to avoid mutation
        data = user_data.copy()
        profile_type = data.pop('profile_type')
        groups = data.pop('groups', [])
        student_data = data.pop('student_data', None)
        faculty_data = data.pop('faculty_data', None)
        
        # Create BaseUser fields only
        user_fields = {
            'username': data['username'],
            'email': data['email'],
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'institutional_id': data['institutional_id'],
            'role_type': data['role_type'],
        }
        
        # Create or get user
        try:
            user = User.objects.get(username=user_fields['username'])
            created = False
            print(f"User already exists: {user.username}")
        except User.DoesNotExist:
            user = User.objects.create_user(**user_fields)
            user.set_password(data['password'])
            user.save()
            created = True
            print(f"Created User: {user.username}")
        
        # Create profile based on type
        if profile_type == 'student' and student_data:
            try:
                student_profile = StudentProfile.objects.get(user=user)
                print(f"StudentProfile already exists for {user.username}")
            except StudentProfile.DoesNotExist:
                student_profile = StudentProfile.objects.create(
                    user=user,
                    program=student_data['program'],
                    section=student_data['section'],
                    year_level=student_data['year_level'],
                    indiv_points=0
                )
                print(f"Created StudentProfile for {user.username}")
                
        elif profile_type == 'faculty' and faculty_data:
            try:
                faculty_profile = FacultyProfile.objects.get(user=user)
                print(f"FacultyProfile already exists for {user.username}")
            except FacultyProfile.DoesNotExist:
                faculty_profile = FacultyProfile.objects.create(
                    user=user,
                    faculty_department=faculty_data['department'],
                    position=faculty_data['position'],
                    hire_date=faculty_data['hire_date']
                )
                print(f"Created FacultyProfile for {user.username}")
        
        # Add to groups
        for group_name in groups:
            from django.contrib.auth.models import Group
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
            print(f"Added {user.username} to group: {group_name}")
        
        created_users[user.username] = user
    
    return created_users

def create_semester():
    """Create a current semester for events using the correct Semester model fields"""
    semester, created = Semester.objects.get_or_create(
        academic_year="2024-2025",
        term="second",  # Using the Term enum value
        defaults={
            'start_date': timezone.now().date() - timedelta(days=30),
            'end_date': timezone.now().date() + timedelta(days=90),
            'is_active': True
        }
    )
    if created:
        print(f"Created Semester: {semester.academic_year} - {semester.get_term_display()}")
    else:
        print(f"Using existing Semester: {semester.academic_year} - {semester.get_term_display()}")
    
    return semester

def create_events(event_types, schedule_blocks, users, semester):
    """Create test events with different statuses"""
    
    events_data = [
        # Proposed Events (awaiting approval)
        {
            "title": "CodeFest 2024",
            "venue": "Computer Lab Building",
            "event_type": event_types[1],  # Competitive
            "event_schedule_block": schedule_blocks[3],  # Full Day
            "sem_id": semester,
            "event_status": Event.EventStatus.proposed,
            "created_by": users['org_officer1'].student_profile
        },
        {
            "title": "Leadership Workshop", 
            "venue": "Main Auditorium",
            "event_type": event_types[0],  # Behavioral
            "event_schedule_block": schedule_blocks[0],  # Morning Session
            "sem_id": semester,
            "event_status": Event.EventStatus.proposed,
            "created_by": users['org_officer2'].student_profile
        },
        
        # Approved Events (current/upcoming)
        {
            "title": "Basketball Tournament",
            "venue": "University Gym",
            "event_type": event_types[1],  # Competitive  
            "event_schedule_block": schedule_blocks[1],  # Afternoon Session
            "sem_id": semester,
            "event_status": Event.EventStatus.approved,
            "created_by": users['org_officer1'].student_profile
        },
        {
            "title": "Mental Health Awareness Seminar",
            "venue": "Room 201, Arts Building", 
            "event_type": event_types[0],  # Behavioral
            "event_schedule_block": schedule_blocks[2],  # Evening Session
            "sem_id": semester,
            "event_status": Event.EventStatus.approved,
            "created_by": users['org_officer2'].student_profile
        },
        
        # Completed Events
        {
            "title": "Programming Competition",
            "venue": "Tech Innovation Center", 
            "event_type": event_types[1],  # Competitive
            "event_schedule_block": schedule_blocks[3],  # Full Day
            "sem_id": semester,
            "event_status": Event.EventStatus.completed,
            "created_by": users['org_officer1'].student_profile
        },
        {
            "title": "Team Building Activity",
            "venue": "University Park",
            "event_type": event_types[0],  # Behavioral
            "event_schedule_block": schedule_blocks[4],  # Weekend Special  
            "sem_id": semester,
            "event_status": Event.EventStatus.completed,
            "created_by": users['org_officer2'].student_profile
        }
    ]
    
    created_events = []
    
    for event_data in events_data:
        created_by = event_data.pop('created_by')
        
        event = Event.objects.create(**event_data)
        created_events.append(event)
        print(f"Created Event: {event.title} ({event.event_status})")
        
        # Create initial schedule for the org officer who created it
        start_time = timezone.now() + timedelta(days=random.randint(1, 30))
        EventSchedule.objects.create(
            event_schedule_block_id=event.event_schedule_block,
            event_id=event,
            user_id=created_by,
            start_time=start_time.time(),
            end_time=(start_time + timedelta(hours=3)).time(),
            creation_date=timezone.now()
        )
    
    return created_events

def create_event_schedules(events, users):
    """Create additional schedules for events"""
    schedules_data = []
    
    for event in events:
        # Each event gets 1-3 additional schedules
        num_schedules = random.randint(1, 3)
        
        for i in range(num_schedules):
            start_date = timezone.now() + timedelta(days=random.randint(1, 60))
            
            schedule = EventSchedule(
                event_schedule_block_id=event.event_schedule_block,
                event_id=event,
                user_id=random.choice([users['org_officer1'].student_profile, 
                                     users['org_officer2'].student_profile]),
                start_time=start_date.time(),
                end_time=(start_date + timedelta(hours=2)).time(),
                creation_date=timezone.now() - timedelta(days=random.randint(1, 10))
            )
            schedules_data.append(schedule)
    
    created_schedules = EventSchedule.objects.bulk_create(schedules_data)
    print(f"Created {len(created_schedules)} additional event schedules")
    return created_schedules

def create_event_approvals(events, users):
    """Create approval records for approved/completed events"""
    approvals_data = []
    
    faculty_users = [users['faculty1'], users['faculty2']]
    
    for event in events:
        if event.event_status in [Event.EventStatus.approved, Event.EventStatus.completed]:
            approval = EventApproval(
                event_id=event,
                approver_id=random.choice(faculty_users).faculty_profile,
                approved_at=timezone.now() - timedelta(days=random.randint(1, 20)),
                notes=random.choice([
                    "Event meets all requirements",
                    "Approved with minor modifications",
                    "Great initiative! Approved",
                    "Budget and venue approved"
                ])
            )
            approvals_data.append(approval)
    
    created_approvals = EventApproval.objects.bulk_create(approvals_data)
    print(f"Created {len(created_approvals)} event approvals")
    return created_approvals

def create_event_attendance(events, users):
    """Create attendance records for events"""
    attendance_data = []
    
    student_users = [users['student1'], users['student2'], users['org_officer1'], users['org_officer2']]
    
    for event in events:
        if event.event_status in [Event.EventStatus.approved, Event.EventStatus.completed]:
            # 2-4 students attend each event
            num_attendees = random.randint(2, 4)
            attendees = random.sample(student_users, min(num_attendees, len(student_users)))
            
            for student_user in attendees:
                time_in = timezone.now() - timedelta(days=random.randint(1, 15))
                attendance = EventAttendance(
                    event_id=event,
                    student_id=student_user.student_profile,
                    time_in=time_in,
                    time_out=time_in + timedelta(hours=2),
                    notes=random.choice([
                        "Attended full session",
                        "Participated actively",
                        "Great engagement",
                        "Completed all activities"
                    ])
                )
                attendance_data.append(attendance)
    
    created_attendance = EventAttendance.objects.bulk_create(attendance_data)
    print(f"Created {len(created_attendance)} attendance records")
    return created_attendance

def main():
    """Main function to run all mock data creation"""
    
    # If you want to clear existing events data, uncomment these lines:
    EventAttendance.objects.all().delete()
    EventApproval.objects.all().delete() 
    EventSchedule.objects.all().delete()
    Event.objects.all().delete()
    print("Cleared all existing events data")
    
    print("=== Creating Event Types ===")
    event_types = create_event_types()
    
    print("\n=== Creating Schedule Blocks ===")
    schedule_blocks = create_schedule_blocks()
    
    print("\n=== Creating Test Users and Profiles ===")
    users = create_test_users_and_profiles()
    
    print("\n=== Creating Semester ===")
    semester = create_semester()
    
    print("\n=== Creating Events ===")
    events = create_events(event_types, schedule_blocks, users, semester)
    
    print("\n=== Creating Event Schedules ===")
    create_event_schedules(events, users)
    
    print("\n=== Creating Event Approvals ===")
    create_event_approvals(events, users)
    
    print("\n=== Creating Event Attendance ===")
    create_event_attendance(events, users)
    
    print("\n" + "="*50)
    print("MOCK DATA GENERATION COMPLETE!")
    print("="*50)
    print("\nTest Accounts Created:")
    print("Org Officers (can create events):")
    print("  - org_officer1 / password123")
    print("  - org_officer2 / password123")
    print("\nRegular Students (can view events and attend):")
    print("  - student1 / password123") 
    print("  - student2 / password123")
    print("\nFaculty (can approve events):")
    print("  - faculty1 / password123")
    print("  - faculty2 / password123")
    print(f"\nTotal Events Created: {len(events)}")
    print("  - 2 Proposed (awaiting approval)")
    print("  - 2 Approved (current/upcoming)")
    print("  - 2 Completed (past events)")

if __name__ == "__main__":
    main()