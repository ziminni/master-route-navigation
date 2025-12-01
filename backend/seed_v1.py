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
# USERS - More comprehensive
# ---------------------------------------------------------------
def create_users():
    # Admin
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

    # Faculty - More faculty members
    faculty_info = [
        ("einstein", "Albert", "Einstein", "CISC"),
        ("lovelace", "Ada", "Lovelace", "CISC"),
        ("torvalds", "Linus", "Torvalds", "CISC"),
        ("knuth", "Donald", "Knuth", "MATH"),
        ("hopper", "Grace", "Hopper", "CISC"),
        ("turing", "Alan", "Turing", "MATH"),
        ("curie", "Marie", "Curie", "SCI"),
        ("newton", "Isaac", "Newton", "MATH"),
    ]
    faculties = []
    for uname, fn, ln, dept in faculty_info:
        user, _ = User.objects.get_or_create(
            username=uname,
            defaults=dict(
                email=f"{uname}@cmu.edu.ph",
                institutional_id=f"FAC{str(len(faculties)+1).zfill(4)}",
                role_type="faculty",
                first_name=fn,
                last_name=ln
            )
        )
        user.set_password("password123")
        user.save()
        user.groups.add(Group.objects.get(name="faculty"))
        faculties.append((user, dept))

    # Students - 36 students (4 years × 3 sections × 3 students)
    student_counter = 1
    students = []
    
    year_levels = [1, 2, 3, 4]
    sections = ['A', 'B', 'C']
    
    for year in year_levels:
        for section in sections:
            for i in range(3):  # 3 students per section
                stud_num = student_counter
                username = f"stud{stud_num:04d}"
                first_name = random.choice(['John', 'Sarah', 'Michael', 'Emily', 'David', 'Lisa', 
                                            'James', 'Maria', 'Robert', 'Jennifer', 'William', 'Karen'])
                last_name = random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia',
                                          'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez'])
                
                user, _ = User.objects.get_or_create(
                    username=username,
                    defaults=dict(
                        email=f"{username}@cmu.edu.ph",
                        institutional_id=f"STU{str(stud_num).zfill(4)}",
                        role_type="student",
                        first_name=first_name,
                        last_name=last_name
                    )
                )
                user.set_password("password123")
                user.save()
                user.groups.add(Group.objects.get(name="student"))
                students.append((user, year, section))
                student_counter += 1

    print(f"✓ Users created: {len(faculties)} faculty, {len(students)} students")
    return faculties, students


# ---------------------------------------------------------------
# PROFILES
# ---------------------------------------------------------------
def create_profiles(faculties, students):
    # Create programs
    programs = []
    for prog_name, abbr in [("BS Information Technology", "BSIT"),
                           ("BS Computer Science", "BSCS"),
                           ("BS Information Systems", "BSIS")]:
        program, _ = Program.objects.get_or_create(
            program_name=prog_name,
            defaults=dict(abbr=abbr)
        )
        programs.append(program)

    # Create user sections (IT-1A, IT-1B, IT-1C, etc.)
    user_sections = {}
    for year in range(1, 5):
        for section in ['A', 'B', 'C']:
            section_name = f"IT-{year}{section}"
            sec, _ = UserSection.objects.get_or_create(section_name=section_name)
            user_sections[(year, section)] = sec

    # Create departments
    departments = {}
    for dept_name in ["CISC", "MATH", "SCI"]:
        dep, _ = FacultyDepartment.objects.get_or_create(department_name=dept_name)
        departments[dept_name] = dep

    # Create positions
    positions = ["Instructor 1", "Instructor 2", "Assistant Professor", "Associate Professor"]
    position_objs = []
    for pos_name in positions:
        pos, _ = Position.objects.get_or_create(position_name=pos_name)
        position_objs.append(pos)

    # Faculty profiles
    faculty_profiles = []
    for fac, dept_name in faculties:
        p, _ = FacultyProfile.objects.get_or_create(
            user=fac,
            defaults=dict(
                faculty_department=departments[dept_name],
                position=random.choice(position_objs),
                hire_date=date(random.randint(2015, 2020), random.randint(1, 12), random.randint(1, 28))
            )
        )
        faculty_profiles.append(p)

    # Student profiles
    student_profiles = []
    for stu, year, section in students:
        sp, _ = StudentProfile.objects.get_or_create(
            user=stu,
            defaults=dict(
                program=random.choice(programs),
                section=user_sections[(year, section)],
                year_level=year
            )
        )
        student_profiles.append(sp)

    print("✓ Profiles created")
    return programs, student_profiles, faculty_profiles, user_sections


# ---------------------------------------------------------------
# ACADEMICS
# ---------------------------------------------------------------
def seed_academics(programs, student_profiles, faculty_profiles, user_sections):
    # Semesters
    sem1, _ = Semester.objects.get_or_create(
        academic_year="2024-2025", term="first",
        start_date=date(2024, 8, 1), end_date=date(2024, 12, 15), defaults=dict(is_active=True)
    )
    sem2, _ = Semester.objects.get_or_create(
        academic_year="2024-2025", term="second",
        start_date=date(2025, 1, 10), end_date=date(2025, 5, 20), defaults=dict(is_active=False)
    )
    
    # Curriculum for BSIT
    it_program = next(p for p in programs if p.abbr == "BSIT")
    curriculum, _ = Curriculum.objects.get_or_create(
        program=it_program, revision_year=2024, defaults=dict(is_active=True)
    )

    # Courses by year level (4 per year)
    courses_by_year = {
        1: [
            ("IT101", "Introduction to Computing", 3, "CISC", 1),
            ("IT102", "Computer Programming 1", 3, "CISC", 1),
            ("MATH101", "Discrete Mathematics", 3, "MATH", 1),
            ("SCI101", "Physical Science", 3, "SCI", 2),
        ],
        2: [
            ("IT201", "Data Structures & Algorithms", 3, "CISC", 1),
            ("IT202", "Object-Oriented Programming", 3, "CISC", 1),
            ("IT203", "Database Management", 3, "CISC", 2),
            ("MATH201", "Calculus 1", 3, "MATH", 2),
        ],
        3: [
            ("IT301", "Operating Systems", 3, "CISC", 1),
            ("IT302", "Computer Networks", 3, "CISC", 1),
            ("IT303", "Web Development", 3, "CISC", 2),
            ("IT304", "Software Engineering", 3, "CISC", 2),
        ],
        4: [
            ("IT401", "Capstone Project 1", 3, "CISC", 1),
            ("IT402", "Capstone Project 2", 3, "CISC", 2),
            ("IT403", "IT Elective 1", 3, "CISC", 1),
            ("IT404", "IT Elective 2", 3, "CISC", 2),
        ]
    }

    # Create all courses
    course_objects = {}
    for year, course_list in courses_by_year.items():
        for code, title, units, dept, term in course_list:
            cc, _ = Course.objects.get_or_create(
                code=code,
                defaults=dict(
                    title=title, 
                    units=units, 
                    lec_hours=units-1 if units > 1 else 0,
                    lab_hours=1 if units > 1 else 0,
                    curriculum=curriculum, 
                    year_offered=str(year),
                    term_offered="first" if term == 1 else "second"
                )
            )
            course_objects[code] = cc

    # Group faculty by department
    faculty_by_dept = {}
    for fp in faculty_profiles:
        dept = fp.faculty_department.department_name
        if dept not in faculty_by_dept:
            faculty_by_dept[dept] = []
        faculty_by_dept[dept].append(fp)

    # Create classes for each semester
    classes = []
    for sem in (sem1, sem2):
        # Academic sections for each year and section
        academic_sections = {}
        for year in range(1, 5):
            for section in ['A', 'B', 'C']:
                sec_name = f"{year}{section}"
                sec, _ = AcademicSection.objects.get_or_create(
                    name=sec_name,
                    curriculum=curriculum,
                    semester=sem,
                    year=str(year),
                    type="lec",
                    defaults=dict(capacity=40)
                )
                academic_sections[(year, section)] = sec

        # Create classes and assign faculty based on course department
        for year, course_list in courses_by_year.items():
            term_courses = []
            # Get courses for this term based on term_offered
            for code, title, units, dept, term in course_list:
                course = course_objects[code]
                if (sem.term == "first" and term == 1) or \
                   (sem.term == "second" and term == 2):
                    term_courses.append((course, dept))

            for section in ['A', 'B', 'C']:
                for course, dept in term_courses:
                    # Assign faculty from matching department
                    available_faculty = faculty_by_dept.get(dept, faculty_by_dept.get("CISC", []))
                    if available_faculty:
                        fac = random.choice(available_faculty)
                    else:
                        fac = random.choice(faculty_profiles)
                    
                    cls, created = Class.objects.get_or_create(
                        course=course,
                        section=academic_sections[(year, section)],
                        semester=sem,
                        defaults=dict(faculty=fac)
                    )
                    classes.append(cls)

    # Enroll students in their classes
    enrollment_count = 0
    for sp in student_profiles:
        # Get student's year and section from user section name
        section_name = sp.section.section_name
        try:
            # Handle format "IT-1A"
            year = int(section_name.split('-')[1][0])  # Extract year from "IT-1A"
            section_letter = section_name.split('-')[1][1]  # Extract "A" from "IT-1A"
        except (IndexError, ValueError):
            # Fallback for different formats
            year = sp.year_level
            section_letter = 'A'  # Default
        
        for cls in classes:
            # Check if class matches student's year and section
            if (cls.section.year == str(year) and 
                cls.section.name == f"{year}{section_letter}" and
                cls.course.year_offered == str(year)):
                
                # Simple enrollment
                enrolled, created = Enrollment.objects.get_or_create(
                    enrolled_class=cls, 
                    student=sp
                )
                if created:
                    enrollment_count += 1

    print(f"✓ Academics seeded: {len(classes)} classes created, {enrollment_count} enrollments")
    return classes


# ---------------------------------------------------------------
# PROGRESS - Fixed to match the original working version
# ---------------------------------------------------------------
def seed_progress(student_profiles, classes):
    grade_count = 0
    feedback_count = 0
    
    for sp in student_profiles:
        section_name = sp.section.section_name
        try:
            year = int(section_name.split('-')[1][0])
            section_letter = section_name.split('-')[1][1]
        except (IndexError, ValueError):
            year = sp.year_level
            section_letter = 'A'
        
        student_classes = []
        for cls in classes:
            if (cls.section.year == str(year) and 
                cls.section.name == f"{year}{section_letter}"):
                student_classes.append(cls)
        
        for cls in student_classes:
            # Check if student is enrolled in this class
            if not Enrollment.objects.filter(enrolled_class=cls, student=sp).exists():
                continue
            
            # Determine if student fails this course (30% chance of failure)
            failed = random.choice([True, False])
            
            # Create final grade - matching the original working version
            fg, created = FinalGrade.objects.get_or_create(
                student=sp.user,
                course=cls.course,
                semester=cls.semester,
                defaults=dict(
                    midterm_grade="2.50" if failed else str(round(random.uniform(1.0, 2.25), 2)),
                    final_term_grade="3.00" if failed else str(round(random.uniform(1.0, 2.25), 2)),
                    final_grade="4.00" if failed else str(round(random.uniform(1.0, 3.0), 2)),  # 4.0 is fail, 1.0-3.0 is pass
                    status="failed" if failed else "passed",
                    re_exam="3.00" if failed else ""  # Only for failed students
                )
            )
            if created:
                grade_count += 1
            
            # Create faculty feedback (1-2 messages per grade, 50% chance)
            if random.random() < 0.5:
                for _ in range(random.randint(1, 2)):
                    ffb, created = FacultyFeedbackMessage.objects.get_or_create(
                        student=sp.user,
                        faculty=cls.faculty.user,
                        grade=fg,
                        defaults=dict(
                            message=random.choice([
                                "Good effort!",
                                "Improve attendance.",
                                "Struggling with quizzes.",
                                "Strong performance!",
                                "Maintain consistency.",
                                f"Good effort in {cls.course.title}!",
                                f"Attendance in {cls.course.code} needs improvement.",
                                f"Excellent performance in quizzes for {cls.course.code}.",
                                f"Struggling with {cls.course.code} assignments.",
                                f"Maintain current performance in {cls.course.title}.",
                                f"Participates actively in {cls.course.code} discussions.",
                                f"Needs to submit {cls.course.code} requirements on time.",
                                f"Shows strong understanding of {cls.course.title} concepts."
                            ])
                        )
                    )
                    if created:
                        feedback_count += 1

    print(f"✓ Progress seeded: {grade_count} grades, {feedback_count} feedback messages")
    print("  Note: Grades 1.0-3.0 = Pass, 4.0+ = Fail")


# ---------------------------------------------------------------
# FACULTY-COURSE ASSIGNMENT SUMMARY
# ---------------------------------------------------------------
def print_faculty_assignments():
    print("\n📋 FACULTY COURSE ASSIGNMENTS:")
    print("-" * 60)
    
    # Get all classes grouped by faculty
    from django.db.models import Count
    from apps.Academics.models import Class
    
    faculty_assignments = {}
    classes = Class.objects.select_related('faculty__user', 'course', 'semester').all()
    
    for cls in classes:
        if cls.faculty:
            fac_name = f"{cls.faculty.user.first_name} {cls.faculty.user.last_name}"
            if fac_name not in faculty_assignments:
                faculty_assignments[fac_name] = []
            faculty_assignments[fac_name].append(
                f"{cls.course.code} - {cls.course.title} ({cls.semester.term} {cls.semester.academic_year})"
            )
    
    for faculty, courses in faculty_assignments.items():
        print(f"\n👨‍🏫 {faculty}:")
        for course in sorted(set(courses)):
            print(f"  • {course}")
    
    print("\n📊 STUDENT DISTRIBUTION:")
    for year in range(1, 5):
        for section in ['A', 'B', 'C']:
            count = StudentProfile.objects.filter(
                section__section_name=f"IT-{year}{section}"
            ).count()
            print(f"  IT-{year}{section}: {count} students")
    
    # Print enrollment and grade statistics
    print(f"\n📈 SYSTEM STATS:")
    total_enrollments = Enrollment.objects.count()
    total_classes = Class.objects.count()
    total_students = StudentProfile.objects.count()
    total_grades = FinalGrade.objects.count()
    total_feedback = FacultyFeedbackMessage.objects.count()
    
    print(f"  Total Enrollments: {total_enrollments}")
    print(f"  Total Classes: {total_classes}")
    print(f"  Total Students: {total_students}")
    print(f"  Total Grades: {total_grades}")
    print(f"  Total Feedback: {total_feedback}")
    
    # Count failing grades
    failing_grades = FinalGrade.objects.filter(status="failed").count()
    passing_grades = FinalGrade.objects.filter(status="passed").count()
    if total_grades > 0:
        fail_percentage = (failing_grades / total_grades) * 100
        print(f"  Failing Grades: {failing_grades} ({fail_percentage:.1f}%)")
        print(f"  Passing Grades: {passing_grades}")
    
    print("-" * 60)


# ---------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------
if __name__ == "__main__":
    print("\n⏳ Seeding database...")
    print("=" * 60)
    
    create_groups()
    faculties, students = create_users()
    programs, student_profiles, faculty_profiles, user_sections = create_profiles(faculties, students)
    classes = seed_academics(programs, student_profiles, faculty_profiles, user_sections)
    seed_progress(student_profiles, classes)
    
    print_faculty_assignments()
    
    print("\n🎉 DATABASE SEEDED SUCCESSFULLY!")
    print("=" * 60)
    print("\n🔑 DEFAULT LOGINS:")
    print("  Admin:     admin / admin123")
    print("  Faculty:   einstein / password123")
    print("  Student:   stud0001 / password123")
    print("\n📚 ACADEMIC STRUCTURE:")
    print("  • 4 Year Levels (1-4)")
    print("  • 3 Sections per year (A, B, C)")
    print("  • 3 Students per section (36 total)")
    print("  • 4 Courses per year level")
    print("  • 2 Semesters (2024-2025)")
    print("  • 8 Faculty members")
    print("  • Faculty assigned to courses by department")
    print("\n📊 GRADING SYSTEM:")
    print("  • Passing: 1.00 - 3.00")
    print("  • Failing: 4.00+")
    print("  • ~30% of students have failing grades")
    print("=" * 60)