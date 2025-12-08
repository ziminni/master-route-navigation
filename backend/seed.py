# backend/seed.py - COMPLETE WORKING VERSION
import os
import django
import random
from datetime import date, datetime, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from apps.Users.models import Program, Section as UserSection, StudentProfile, FacultyProfile, FacultyDepartment, Position
from apps.Academics.models import Semester, Curriculum, Course, Section as AcademicSection, Class, Enrollment
from apps.Progress.models import FinalGrade, FacultyFeedbackMessage, ClassScheduleInfo

User = get_user_model()


# ---------------------------------------------------------------
# 1. CREATE GROUPS
# ---------------------------------------------------------------
def create_groups():
    print("1. Creating groups...")
    for role in ("admin", "faculty", "staff", "student", "org_officer"):
        Group.objects.get_or_create(name=role)
    print("   ✓ Groups created")


# ---------------------------------------------------------------
# 2. CREATE USERS
# ---------------------------------------------------------------
def create_users():
    print("\n2. Creating users...")
    
    # Admin
    admin, created = User.objects.get_or_create(
        username="admin",
        defaults=dict(
            email="admin@cmu.edu.ph",
            institutional_id="ADM0001",
            role_type="admin",
            first_name="Admin",
            last_name="User",
            is_superuser=True,
            is_staff=True
        )
    )
    if created:
        admin.set_password("admin123")
        admin.save()
    admin.groups.add(Group.objects.get(name="admin"))
    print("   ✓ Admin created: admin / admin123")
    
    # Faculty
    faculty_list = [
        ("einstein", "Albert", "Einstein", "albert@cmu.edu.ph", "CISC"),
        ("lovelace", "Ada", "Lovelace", "ada@cmu.edu.ph", "CISC"),
        ("torvalds", "Linus", "Torvalds", "linus@cmu.edu.ph", "CISC"),
        ("knuth", "Donald", "Knuth", "donald@cmu.edu.ph", "MATH"),
        ("hopper", "Grace", "Hopper", "grace@cmu.edu.ph", "CISC"),
        ("turing", "Alan", "Turing", "alan@cmu.edu.ph", "MATH"),
        ("curie", "Marie", "Curie", "marie@cmu.edu.ph", "SCI"),
        ("newton", "Isaac", "Newton", "isaac@cmu.edu.ph", "MATH"),
    ]
    
    faculties = []
    for i, (uname, fname, lname, email, dept) in enumerate(faculty_list, 1):
        user, created = User.objects.get_or_create(
            username=uname,
            defaults=dict(
                email=email,
                institutional_id=f"FAC{str(i).zfill(4)}",
                role_type="faculty",
                first_name=fname,
                last_name=lname
            )
        )
        if created:
            user.set_password("password123")
            user.save()
        user.groups.add(Group.objects.get(name="faculty"))
        faculties.append((user, dept))
        print(f"   ✓ Faculty {i}: {uname} / password123")
    
    # Students (36 total: 4 years × 3 sections × 3 students)
    print("\n3. Creating students...")
    first_names = ['John', 'Sarah', 'Michael', 'Emily', 'David', 'Lisa', 
                   'James', 'Maria', 'Robert', 'Jennifer', 'William', 'Karen']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia',
                  'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez']
    
    students = []
    student_counter = 1
    
    for year in range(1, 5):  # Years 1-4
        for section in ['A', 'B', 'C']:  # Sections A, B, C
            for i in range(3):  # 3 students per section
                stud_num = student_counter
                username = f"stud{stud_num:04d}"
                fname = random.choice(first_names)
                lname = random.choice(last_names)
                
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults=dict(
                        email=f"{username}@cmu.edu.ph",
                        institutional_id=f"STU{str(stud_num).zfill(4)}",
                        role_type="student",
                        first_name=fname,
                        last_name=lname
                    )
                )
                if created:
                    user.set_password("password123")
                    user.save()
                user.groups.add(Group.objects.get(name="student"))
                students.append((user, year, section))
                student_counter += 1
                
                if stud_num <= 5:  # Show first 5
                    print(f"   ✓ Student {stud_num}: {username} / password123")
    
    print(f"   Total: {len(students)} students created")
    return faculties, students


# ---------------------------------------------------------------
# 3. CREATE PROGRAMS & PROFILES
# ---------------------------------------------------------------
def create_profiles(faculties, students):
    print("\n4. Creating programs and profiles...")
    
    # Create programs
    programs = []
    for prog_name in ["BS Information Technology", "BS Computer Science", "BS Information Systems"]:
        program, created = Program.objects.get_or_create(program_name=prog_name)
        programs.append(program)
        print(f"   ✓ Program: {prog_name}")
    
    # Create user sections (IT-1A, IT-1B, etc.)
    user_sections = {}
    for year in range(1, 5):
        for section in ['A', 'B', 'C']:
            section_name = f"IT-{year}{section}"
            sec, created = UserSection.objects.get_or_create(section_name=section_name)
            user_sections[(year, section)] = sec
    
    print(f"   ✓ Created {len(user_sections)} user sections")
    
    # Create departments
    departments = {}
    for dept_name in ["CISC", "MATH", "SCI"]:
        dep, created = FacultyDepartment.objects.get_or_create(department_name=dept_name)
        departments[dept_name] = dep
    
    # Create positions
    positions = ["Instructor 1", "Instructor 2", "Assistant Professor", "Associate Professor"]
    position_objs = []
    for pos_name in positions:
        pos, created = Position.objects.get_or_create(position_name=pos_name)
        position_objs.append(pos)
    
    # Create faculty profiles
    faculty_profiles = []
    for user, dept_name in faculties:
        profile, created = FacultyProfile.objects.get_or_create(
            user=user,
            defaults=dict(
                faculty_department=departments.get(dept_name, departments["CISC"]),
                position=random.choice(position_objs),
                hire_date=date(random.randint(2015, 2020), random.randint(1, 12), random.randint(1, 28))
            )
        )
        faculty_profiles.append(profile)
    
    print(f"   ✓ Created {len(faculty_profiles)} faculty profiles")
    
    # Create student profiles
    student_profiles = []
    for user, year, section in students:
        profile, created = StudentProfile.objects.get_or_create(
            user=user,
            defaults=dict(
                program=random.choice(programs),
                section=user_sections[(year, section)],
                year_level=year,
                indiv_points=random.randint(0, 100)
            )
        )
        student_profiles.append(profile)
    
    print(f"   ✓ Created {len(student_profiles)} student profiles")
    return programs, student_profiles, faculty_profiles, user_sections


# ---------------------------------------------------------------
# 4. CREATE ACADEMIC DATA
# ---------------------------------------------------------------
def seed_academics(programs, student_profiles, faculty_profiles, user_sections):
    print("\n5. Creating academic data...")
    
    # Get BSIT program
    it_program = None
    for prog in programs:
        if "Information Technology" in prog.program_name:
            it_program = prog
            break
    
    if not it_program:
        it_program, _ = Program.objects.get_or_create(program_name="BS Information Technology")
        programs.append(it_program)
    
    # Create semesters
    sem1, created = Semester.objects.get_or_create(
        academic_year="2024-2025",
        term="first",
        defaults=dict(
            start_date=date(2024, 8, 1),
            end_date=date(2024, 12, 15),
            is_active=True
        )
    )
    
    sem2, created = Semester.objects.get_or_create(
        academic_year="2024-2025",
        term="second",
        defaults=dict(
            start_date=date(2025, 1, 10),
            end_date=date(2025, 5, 20),
            is_active=False
        )
    )
    
    print(f"   ✓ Semesters: {sem1.term} & {sem2.term}")
    
    # Create curriculum
    curriculum, created = Curriculum.objects.get_or_create(
        program=it_program,
        revision_year=2024,
        defaults=dict(is_active=True)
    )
    print("   ✓ Curriculum created")
    
    # Create courses
    courses_data = {
        1: [
            ("IT101", "Introduction to Computing", 3),
            ("IT102", "Computer Programming 1", 3),
            ("MATH101", "Discrete Mathematics", 3),
            ("SCI101", "Physical Science", 3),
        ],
        2: [
            ("IT201", "Data Structures & Algorithms", 3),
            ("IT202", "Object-Oriented Programming", 3),
            ("IT203", "Database Management", 3),
            ("MATH201", "Calculus 1", 3),
        ],
        3: [
            ("IT301", "Operating Systems", 3),
            ("IT302", "Computer Networks", 3),
            ("IT303", "Web Development", 3),
            ("IT304", "Software Engineering", 3),
        ],
        4: [
            ("IT401", "Capstone Project 1", 3),
            ("IT402", "Capstone Project 2", 3),
            ("IT403", "IT Elective 1", 3),
            ("IT404", "IT Elective 2", 3),
        ]
    }
    
    course_objects = {}
    for year, course_list in courses_data.items():
        for code, title, units in course_list:
            course, created = Course.objects.get_or_create(
                code=code,
                defaults=dict(
                    title=title,
                    units=units,
                    lec_hours=units - 1 if units > 1 else 0,
                    lab_hours=1 if units > 1 else 0,
                    curriculum=curriculum,
                    year_offered=str(year),
                    term_offered="first" if year % 2 == 1 else "second"
                )
            )
            course_objects[code] = course
    
    print(f"   ✓ Created {len(course_objects)} courses")
    
    # Create academic sections and classes
    all_classes = []
    
    for semester in [sem1, sem2]:
        # Create academic sections for this semester
        academic_sections = {}
        for year in range(1, 5):
            for section in ['A', 'B', 'C']:
                section_name = f"{year}{section}"
                academic_section, created = AcademicSection.objects.get_or_create(
                    name=section_name,
                    curriculum=curriculum,
                    semester=semester,
                    defaults=dict(
                        year=str(year),
                        type="lec",
                        capacity=40
                    )
                )
                academic_sections[(year, section)] = academic_section
        
        # Create classes for each academic section
        for (year, section), academic_section in academic_sections.items():
            # Get courses for this year
            year_courses = []
            for code, course in course_objects.items():
                if course.year_offered == str(year):
                    year_courses.append(course)
            
            # Assign 2 courses per semester (alternating)
            if semester.term == "first" and year % 2 == 1:
                selected_courses = year_courses[:2]  # First 2 courses in 1st sem
            elif semester.term == "second" and year % 2 == 0:
                selected_courses = year_courses[2:]  # Last 2 courses in 2nd sem
            else:
                continue  # Skip if not the right semester for this year
            
            for course in selected_courses:
                # Assign random faculty
                faculty_profile = random.choice(faculty_profiles)
                
                # Create class
                class_obj, created = Class.objects.get_or_create(
                    course=course,
                    section=academic_section,
                    semester=semester,
                    defaults=dict(faculty=faculty_profile)
                )
                all_classes.append(class_obj)
    
    print(f"   ✓ Created {len(all_classes)} classes")
    
    # Enroll students
    enrollment_count = 0
    for student_profile in student_profiles:
        # Get student's year and section
        section_name = student_profile.section.section_name
        try:
            # Format: "IT-1A" -> year=1, section="A"
            year = int(section_name.split('-')[1][0])
            section_letter = section_name.split('-')[1][1]
        except:
            year = student_profile.year_level
            section_letter = 'A'
        
        # Find matching classes
        for class_obj in all_classes:
            if (class_obj.section.year == str(year) and 
                class_obj.section.name == f"{year}{section_letter}"):
                
                # Enroll student
                enrollment, created = Enrollment.objects.get_or_create(
                    enrolled_class=class_obj,
                    student=student_profile
                )
                if created:
                    enrollment_count += 1
    
    print(f"   ✓ Created {enrollment_count} enrollments")
    return all_classes


# ---------------------------------------------------------------
# 5. CREATE SCHEDULE INFO
# ---------------------------------------------------------------
def seed_schedule_info(classes):
    print("\n6. Creating schedule information...")
    
    admin_user = User.objects.get(username="admin")
    
    schedules = [
        ("MWF", "8:00-9:00 AM"),
        ("MWF", "9:00-10:00 AM"),
        ("MWF", "10:00-11:00 AM"),
        ("MWF", "1:00-2:00 PM"),
        ("MWF", "2:00-3:00 PM"),
        ("TTH", "8:00-9:30 AM"),
        ("TTH", "9:30-11:00 AM"),
        ("TTH", "1:00-2:30 PM"),
        ("TTH", "2:30-4:00 PM"),
        ("SAT", "8:00-11:00 AM"),
    ]
    
    rooms = [
        "Room 101", "Room 102", "Room 103", "Room 104",
        "Room 201", "Room 202", "Room 203", "Room 204",
        "Room 301", "Room 302", "Room 303", "Room 304",
        "Lab 1", "Lab 2", "Lab 3", "Lab 4",
        "Computer Lab A", "Computer Lab B", "Computer Lab C",
    ]
    
    schedule_count = 0
    for i, class_obj in enumerate(classes):
        try:
            schedule_idx = i % len(schedules)
            room_idx = i % len(rooms)
            schedule_days, schedule_time = schedules[schedule_idx]
            room = rooms[room_idx]
            full_schedule = f"{schedule_days} {schedule_time}"
            
            schedule_info, created = ClassScheduleInfo.objects.get_or_create(
                class_instance=class_obj,
                defaults=dict(
                    schedule=full_schedule,
                    room=room,
                    updated_by=admin_user
                )
            )
            
            if created:
                schedule_count += 1
        except Exception as e:
            print(f"   ⚠ Error creating schedule for class {class_obj.id}: {e}")
    
    print(f"   ✓ Created {schedule_count} schedule entries")
    return schedule_count


# ---------------------------------------------------------------
# 6. CREATE PROGRESS DATA (Grades & Feedback)
# ---------------------------------------------------------------
def seed_progress(student_profiles, classes):
    print("\n7. Creating progress data (grades & feedback)...")
    
    grade_count = 0
    feedback_count = 0
    
    for student_profile in student_profiles:
        # Get student's classes
        student_classes = []
        for class_obj in classes:
            # Check if student is enrolled in this class
            if Enrollment.objects.filter(enrolled_class=class_obj, student=student_profile).exists():
                student_classes.append(class_obj)
        
        for class_obj in student_classes:
            # Determine if student fails (30% chance)
            failed = random.random() < 0.3
            
            # Calculate grades
            if failed:
                midterm = round(random.uniform(3.0, 4.0), 2)
                final_term = round(random.uniform(3.0, 4.0), 2)
                final_grade = round(random.uniform(3.5, 5.0), 2)
                status = "failed"
                re_exam = "3.00"
            else:
                midterm = round(random.uniform(1.0, 2.5), 2)
                final_term = round(random.uniform(1.0, 2.5), 2)
                final_grade = round(random.uniform(1.0, 3.0), 2)
                status = "passed"
                re_exam = ""
            
            # Create final grade
            fg, created = FinalGrade.objects.get_or_create(
                student=student_profile.user,
                course=class_obj.course,
                semester=class_obj.semester,
                defaults=dict(
                    midterm_grade=str(midterm),
                    final_term_grade=str(final_term),
                    final_grade=str(final_grade),
                    status=status,
                    re_exam=re_exam
                )
            )
            
            if created:
                grade_count += 1
            
            # Create faculty feedback (50% chance)
            if random.random() < 0.5:
                message = random.choice([
                    f"Good effort in {class_obj.course.title}!",
                    f"Attendance in {class_obj.course.code} needs improvement.",
                    f"Excellent performance in quizzes for {class_obj.course.code}.",
                    f"Struggling with {class_obj.course.code} assignments.",
                    f"Maintain current performance in {class_obj.course.title}.",
                    f"Participates actively in {class_obj.course.code} discussions.",
                    f"Needs to submit {class_obj.course.code} requirements on time.",
                    f"Shows strong understanding of {class_obj.course.title} concepts."
                ])
                
                ffb, created = FacultyFeedbackMessage.objects.get_or_create(
                    student=student_profile.user,
                    faculty=class_obj.faculty.user,
                    grade=fg,
                    message=message,
                    defaults=dict(date_sent=date.today())
                )
                
                if created:
                    feedback_count += 1
    
    print(f"   ✓ Created {grade_count} final grades")
    print(f"   ✓ Created {feedback_count} faculty feedback messages")
    return grade_count, feedback_count


# ---------------------------------------------------------------
# 7. PRINT SUMMARY
# ---------------------------------------------------------------
def print_summary():
    print("\n" + "="*60)
    print("DATABASE SEEDING COMPLETE!")
    print("="*60)
    
    print("\n📊 DATABASE STATISTICS:")
    print(f"  • Users: {User.objects.count()} total")
    print(f"  • Faculty: {User.objects.filter(role_type='faculty').count()}")
    print(f"  • Students: {User.objects.filter(role_type='student').count()}")
    print(f"  • Programs: {Program.objects.count()}")
    print(f"  • Courses: {Course.objects.count()}")
    print(f"  • Classes: {Class.objects.count()}")
    print(f"  • Enrollments: {Enrollment.objects.count()}")
    print(f"  • Final Grades: {FinalGrade.objects.count()}")
    
    print("\n🔑 DEFAULT LOGINS:")
    print("  Admin:     admin / admin123")
    print("  Faculty:   einstein / password123")
    print("  Student:   stud0001 / password123")
    
    print("\n📚 ACADEMIC STRUCTURE:")
    print("  • Programs: BS Information Technology, BS Computer Science, BS Information Systems")
    print("  • Year Levels: 1-4 (4 years)")
    print("  • Sections per year: A, B, C (3 sections)")
    print("  • Students: 36 total (3 per section)")
    print("  • Courses: 4 per year level (16 total)")
    print("  • Semesters: 2024-2025 (1st & 2nd)")
    
    print("\n📊 GRADING:")
    print("  • Passing: 1.00 - 3.00")
    print("  • Failing: 3.50 - 5.00")
    print("  • ~30% of students have failing grades")
    
    print("\n" + "="*60)


# ---------------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "="*60)
    print("STARTING DATABASE SEEDING")
    print("="*60)
    
    try:
        # Step 1: Create groups
        create_groups()
        
        # Step 2: Create users
        faculties, students = create_users()
        
        # Step 3: Create profiles
        programs, student_profiles, faculty_profiles, user_sections = create_profiles(faculties, students)
        
        # Step 4: Create academic data
        classes = seed_academics(programs, student_profiles, faculty_profiles, user_sections)
        
        # Step 5: Create schedule info
        seed_schedule_info(classes)
        
        # Step 6: Create progress data
        seed_progress(student_profiles, classes)
        
        # Step 7: Print summary
        print_summary()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*60)
        print("SEEDING FAILED!")
        print("="*60)