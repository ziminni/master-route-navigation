# backend/apps/Progress/views_admin.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from apps.Academics.models import Section, Enrollment, Class, Course, Semester
from apps.Users.models import StudentProfile
from .models import FinalGrade, FacultyFeedbackMessage


def calculate_student_progress(student_profile):
    """Calculate actual degree progress percentages for different categories"""
    try:
        # Get all final grades for this student
        final_grades = FinalGrade.objects.filter(student=student_profile.user).select_related('course')
        total_courses = final_grades.count()
        
        if total_courses == 0:
            return {
                "Core Courses": 0,
                "Electives": 0,
                "Capstone Project": 0,
                "Internship": 0,
                "General Education": 0
            }
        
        # Initialize counters
        core_count = 0
        elective_count = 0
        capstone_count = 0
        internship_count = 0
        ge_count = 0
        
        # Categorize passed courses
        for grade in final_grades:
            if grade.status.lower() == "passed" and grade.course:
                course_code = grade.course.code.upper() if grade.course.code else ""
                course_title = grade.course.title.upper() if grade.course.title else ""
                
                # Categorize based on course code/title patterns
                # General Education courses
                if "GE" in course_code or "GENERAL" in course_title or "LIBERAL" in course_title:
                    ge_count += 1
                # Capstone/Thesis courses
                elif "CAPSTONE" in course_title or "THESIS" in course_title or "PROJECT" in course_title:
                    capstone_count += 1
                # Internship/Practicum courses
                elif "INTERNSHIP" in course_title or "PRACTICUM" in course_title or "FIELD" in course_title:
                    internship_count += 1
                # Elective courses (typically codes like ELEC, ELECT, or "ELECTIVE" in title)
                elif "ELECT" in course_code or "ELECTIVE" in course_title or "OPTIONAL" in course_title:
                    elective_count += 1
                # Core courses (everything else)
                else:
                    core_count += 1
        
        # Get total requirements (these should ideally come from the curriculum)
        # For now, use reasonable defaults based on typical 4-year programs
        requirements = {
            "Core Courses": 40,    # ~40 core courses in a 4-year program
            "Electives": 10,       # ~10 elective courses
            "Capstone Project": 1, # 1 capstone project
            "Internship": 1,       # 1 internship
            "General Education": 20 # ~20 GE courses
        }
        
        # Calculate percentages
        progress = {
            "Core Courses": min(100, int((core_count / requirements["Core Courses"]) * 100)) if requirements["Core Courses"] > 0 else 0,
            "Electives": min(100, int((elective_count / requirements["Electives"]) * 100)) if requirements["Electives"] > 0 else 0,
            "Capstone Project": 100 if capstone_count >= requirements["Capstone Project"] else 0,
            "Internship": 100 if internship_count >= requirements["Internship"] else 0,
            "General Education": min(100, int((ge_count / requirements["General Education"]) * 100)) if requirements["General Education"] > 0 else 0
        }
        
        return progress
    except Exception as e:
        print(f"DEBUG: Error calculating progress: {e}")
        # Fallback to reasonable defaults if calculation fails
        return {
            "Core Courses": 25,
            "Electives": 25,
            "Capstone Project": 0,
            "Internship": 0,
            "General Education": 25
        }


class AdminSectionsAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if getattr(request.user, "role_type", "") != "admin":
            return Response({"detail": "Forbidden"}, status=403)

        sections = (
            Section.objects
            .select_related("semester", "curriculum")
            .annotate(student_count=Count("classes__enrollments", distinct=True))
        )

        year_map = {}
        for s in sections:
            year = getattr(s, "year_level", "") or "All Years"
            if year not in year_map:
                year_map[year] = []
            
            year_map[year].append({
                "section_name": getattr(s, "name", ""),
                "image": getattr(s, "image_path", "") if hasattr(s, "image_path") else "",
                "students": getattr(s, "student_count", 0)
            })

        return Response({"year_levels": year_map}, status=200)


class AdminSectionStudentsAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, section_name):
        if getattr(request.user, "role_type", "") != "admin":
            return Response({"detail": "Forbidden"}, status=403)

        print(f"DEBUG: Fetching students for section: {section_name}")
        
        # Find academic sections with this name
        sections = Section.objects.filter(name=section_name)
        if not sections.exists():
            print(f"DEBUG: No sections found with name: {section_name}")
            return Response({"students": []}, status=200)

        # Get enrollments for this section
        enrollments = Enrollment.objects.filter(
            enrolled_class__section__in=sections
        ).select_related("student", "student__user")
        
        print(f"DEBUG: Found {enrollments.count()} enrollments")
        
        # Manually filter unique students
        unique_students = {}
        for e in enrollments:
            user_id = e.student.user.id
            if user_id not in unique_students:
                unique_students[user_id] = e

        print(f"DEBUG: Unique students found: {len(unique_students)}")
        
        result = []
        for user_id, e in unique_students.items():
            user = e.student.user
            
            # Get all final grades for this student
            final_grades = FinalGrade.objects.filter(student=user)
            
            # Calculate GWA (simple average)
            gwa_vals = []
            for fg in final_grades:
                try:
                    if fg.final_grade:
                        grade_value = float(fg.final_grade)
                        gwa_vals.append(grade_value)
                except (ValueError, TypeError):
                    pass
            
            gwa = round(sum(gwa_vals) / len(gwa_vals), 2) if gwa_vals else ""
            
            # Check if any failed
            has_failed = final_grades.filter(status__iexact="failed").exists()
            remarks = "FAILED" if has_failed else "PASSED"
            
            # Use institutional_id as student_id
            student_id = user.institutional_id or user.username
            
            result.append({
                "student_id": student_id,
                "name": f"{user.first_name} {user.last_name}",
                "grade": gwa,
                "remarks": remarks,
                "gwa": gwa,
                "missing_requirement": "",
            })

        print(f"DEBUG: Returning {len(result)} students")
        return Response({"students": result}, status=200)


class AdminStudentProfileAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        if getattr(request.user, "role_type", "") != "admin":
            return Response({"detail": "Forbidden"}, status=403)
        
        print(f"DEBUG: Fetching profile for identifier: {student_id}")
        
        try:
            # FIXED: Use "program" not "course" for select_related
            student_profile = StudentProfile.objects.select_related("program", "user").get(
                Q(user__username=student_id) | 
                Q(user__institutional_id=student_id)
            )
        except StudentProfile.DoesNotExist:
            print(f"DEBUG: Student not found with identifier: {student_id}")
            return Response({"detail": "Student not found."}, status=404)
        
        user = student_profile.user
        print(f"DEBUG: Found student: {user.get_full_name()} (username: {user.username}, institutional_id: {user.institutional_id})")
        
        # Get final grades
        final_grades = FinalGrade.objects.filter(student=user).select_related("course", "semester")
        print(f"DEBUG: Found {final_grades.count()} final grades")
        
        grades_data = []
        for g in final_grades:
            grades_data.append({
                "subject_code": g.course.code if g.course else "",
                "description": g.course.title if g.course else "",
                "units": g.course.units if g.course else 0,
                "midterm": g.midterm_grade or "",
                "finals": g.final_term_grade or g.final_grade or "",
            })
        
        # Calculate progress using the new function
        progress = calculate_student_progress(student_profile)
        
        # Get faculty notes
        notes = FacultyFeedbackMessage.objects.filter(
            student=user
        ).select_related("faculty", "grade", "grade__course").order_by("-date_sent")
        
        notes_data = []
        for note in notes:
            notes_data.append({
                "faculty": note.faculty.get_full_name() if note.faculty else "Unknown",
                "subject": note.grade.course.code if note.grade and note.grade.course else "No Subject",
                "message": note.message,
                "date": note.date_sent.strftime("%b %d, %Y") if note.date_sent else "",
            })
        
        response_data = {
            "student_name": user.get_full_name(),
            "name": user.get_full_name(),
            "student_id": user.institutional_id or user.username,
            "course": student_profile.program.program_name if student_profile.program else "",
            "grades": grades_data,
            "progress": progress,
            "notes": notes_data,
        }
        
        print(f"DEBUG: Returning profile data")
        return Response(response_data, status=200)