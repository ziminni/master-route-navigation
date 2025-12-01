# backend/apps/Progress/views_faculty.py
"""
Faculty-specific views for Progress module.
These endpoints are only accessible to faculty users.
"""
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.Academics.models import Class, Enrollment, Section, Course, Semester
from apps.Users.models import FacultyProfile, StudentProfile
from .models import FinalGrade, FacultyFeedbackMessage
from .serializers import FacultyFeedbackMessageSerializer


class FacultySectionsAPIView(APIView):
    """
    GET /api/progress/faculty/sections/
    Returns sections assigned to the logged-in faculty member.
    Only shows sections where faculty is teaching classes.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Ensure user is faculty
        if getattr(user, "role_type", "") != "faculty":
            return Response({"detail": "Forbidden. Faculty access only."}, status=403)
        
        try:
            # Get faculty profile
            faculty_profile = FacultyProfile.objects.get(user=user)
            
            # Get all classes taught by this faculty
            faculty_classes = Class.objects.filter(faculty=faculty_profile)
            
            # Get unique sections from these classes
            section_ids = faculty_classes.values_list('section', flat=True).distinct()
            sections = Section.objects.filter(id__in=section_ids).select_related('semester', 'curriculum')
            
            # Group sections by year level
            year_levels = {}
            
            for section in sections:
                # FIXED: Try to get year from section or use default
                # Check if section has year field (from your AcademicSection model)
                year_level = getattr(section, 'year', None)
                
                # If not found, try from section name pattern (e.g., "BSIT-1A" -> "1st Year")
                if not year_level:
                    section_name = getattr(section, "name", "")
                    if section_name:
                        # Extract year from section name like "BSIT-1A" or "IT-1A"
                        import re
                        match = re.search(r'-(\d+)', section_name)
                        if match:
                            year_num = int(match.group(1))
                            year_level = f"{year_num}st Year" if year_num == 1 else f"{year_num}nd Year" if year_num == 2 else f"{year_num}rd Year" if year_num == 3 else f"{year_num}th Year"
                
                # Default if still not found
                year_label = year_level or "All Years"
                
                # Count students in this section through enrollments
                student_count = Enrollment.objects.filter(
                    enrolled_class__section=section
                ).values('student').distinct().count()
                
                section_data = {
                    "section_name": getattr(section, "name", ""),
                    "image": getattr(section, "image_path", "") if hasattr(section, "image_path") else "",
                    "students": student_count
                }
                
                if year_label not in year_levels:
                    year_levels[year_label] = []
                
                year_levels[year_label].append(section_data)
            
            # If no sections found, return empty
            if not year_levels:
                return Response({"year_levels": {}}, status=200)
            
            return Response({"year_levels": year_levels}, status=200)
            
        except FacultyProfile.DoesNotExist:
            return Response({"detail": "Faculty profile not found."}, status=404)
        except Exception as e:
            print(f"ERROR in FacultySectionsAPIView: {str(e)}")
            return Response({"detail": f"Error: {str(e)}"}, status=500)


class FacultySectionStudentsAPIView(APIView):
    """
    GET /api/progress/faculty/section/<str:section_name>/students/
    Returns students in a specific section that the faculty teaches.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, section_name):
        user = request.user
        
        # Ensure user is faculty
        if getattr(user, "role_type", "") != "faculty":
            return Response({"detail": "Forbidden. Faculty access only."}, status=403)
        
        try:
            faculty_profile = FacultyProfile.objects.get(user=user)
            
            # Find sections with this name that the faculty teaches
            faculty_sections = Section.objects.filter(
                name=section_name,
                classes__faculty=faculty_profile
            ).distinct()
            
            if not faculty_sections.exists():
                return Response({
                    "detail": "You don't have access to this section or it doesn't exist."
                }, status=403)
            
            # Get enrollments for this section
            enrollments = Enrollment.objects.filter(
                enrolled_class__section__in=faculty_sections
            ).select_related("student", "student__user")
            
            # Get unique students
            unique_students = {}
            for e in enrollments:
                user_id = e.student.user.id
                if user_id not in unique_students:
                    unique_students[user_id] = e

            # Prepare student data
            students_list = []
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
                
                students_list.append({
                    "student_id": student_id,
                    "name": f"{user.first_name} {user.last_name}",
                    "grade": gwa,
                    "remarks": remarks,
                    "gwa": gwa,
                    "missing_requirement": "",
                })

            return Response({"students": students_list}, status=200)
            
        except FacultyProfile.DoesNotExist:
            return Response({"detail": "Faculty profile not found."}, status=404)
        except Exception as e:
            print(f"ERROR in FacultySectionStudentsAPIView: {str(e)}")
            return Response({"detail": f"Error: {str(e)}"}, status=500)


class FacultyStudentProfileAPIView(APIView):
    """
    GET /api/progress/faculty/student/<str:student_id>/profile/
    Returns profile of a student that the faculty teaches.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        user = request.user
        
        # Ensure user is faculty
        if getattr(user, "role_type", "") != "faculty":
            return Response({"detail": "Forbidden. Faculty access only."}, status=403)
        
        try:
            faculty_profile = FacultyProfile.objects.get(user=user)
            
            # Find the student
            student_profile = StudentProfile.objects.select_related("program", "user").get(
                Q(user__username=student_id) | 
                Q(user__institutional_id=student_id)
            )
            
            # Check if faculty teaches this student
            teaches_student = Class.objects.filter(
                faculty=faculty_profile,
                enrollments__student=student_profile
            ).exists()
            
            if not teaches_student:
                return Response({
                    "detail": "You don't teach this student."
                }, status=403)
            
            student_user = student_profile.user
            
            # Get final grades for courses the faculty teaches to this student
            faculty_courses = Class.objects.filter(
                faculty=faculty_profile,
                enrollments__student=student_profile
            ).values_list('course', flat=True).distinct()
            
            final_grades = FinalGrade.objects.filter(
                student=student_user,
                course__in=faculty_courses
            ).select_related("course", "semester")
            
            # Prepare grades data
            grades_data = []
            for g in final_grades:
                grades_data.append({
                    "id": g.grade_id,  # Include grade_id for note sending
                    "subject_code": g.course.code if g.course else "",
                    "description": g.course.title if g.course else "",
                    "units": g.course.units if g.course else 0,
                    "midterm": g.midterm_grade or "",
                    "finals": g.final_term_grade or g.final_grade or "",
                })
            
            # Calculate student progress (simplified version)
            def calculate_student_progress(student_profile):
                """Calculate degree progress for faculty view"""
                try:
                    final_grades_all = FinalGrade.objects.filter(student=student_profile.user)
                    total_courses = final_grades_all.count()
                    
                    if total_courses == 0:
                        return {
                            "Core Courses": 25,
                            "Electives": 25,
                            "General Education": 25
                        }
                    
                    # Count by category
                    core_count = 0
                    elective_count = 0
                    ge_count = 0
                    
                    for grade in final_grades_all:
                        if grade.status.lower() == "passed" and grade.course:
                            course_code = grade.course.code.upper() if grade.course.code else ""
                            course_title = grade.course.title.upper() if grade.course.title else ""
                            
                            if "GE" in course_code or "GENERAL" in course_title:
                                ge_count += 1
                            elif "ELECT" in course_code or "ELECTIVE" in course_title:
                                elective_count += 1
                            else:
                                core_count += 1
                    
                    # Calculate percentages based on typical requirements
                    requirements = {
                        "Core Courses": 40,
                        "Electives": 10,
                        "General Education": 20
                    }
                    
                    progress = {
                        "Core Courses": min(100, int((core_count / requirements["Core Courses"]) * 100)) if requirements["Core Courses"] > 0 else 0,
                        "Electives": min(100, int((elective_count / requirements["Electives"]) * 100)) if requirements["Electives"] > 0 else 0,
                        "General Education": min(100, int((ge_count / requirements["General Education"]) * 100)) if requirements["General Education"] > 0 else 0
                    }
                    
                    return progress
                except Exception as e:
                    print(f"Error calculating progress: {e}")
                    return {
                        "Core Courses": 25,
                        "Electives": 25,
                        "General Education": 25
                    }
            
            progress = calculate_student_progress(student_profile)
            
            # Get faculty notes (only those sent by this faculty to this student)
            notes = FacultyFeedbackMessage.objects.filter(
                student=student_user,
                faculty=user
            ).select_related("faculty", "grade", "grade__course").order_by("-date_sent")
            
            notes_data = []
            for note in notes:
                notes_data.append({
                    "id": note.id,
                    "faculty": note.faculty.get_full_name() if note.faculty else "Unknown",
                    "faculty_name": note.faculty.get_full_name() if note.faculty else "Unknown",
                    "subject": note.grade.course.code if note.grade and note.grade.course else "General Feedback",
                    "message": note.message,
                    "date_sent": note.date_sent.isoformat() if note.date_sent else "",
                    "date": note.date_sent.strftime("%b %d, %Y") if note.date_sent else "",
                })
            
            response_data = {
                "student_name": student_user.get_full_name(),
                "name": student_user.get_full_name(),
                "student_id": student_user.institutional_id or student_user.username,
                "user_id": student_user.id,  # Add user_id for note sending
                "course": student_profile.program.program_name if student_profile.program else "",
                "grades": grades_data,
                "progress": progress,
                "notes": notes_data,
            }
            
            return Response(response_data, status=200)
            
        except StudentProfile.DoesNotExist:
            return Response({"detail": "Student not found."}, status=404)
        except FacultyProfile.DoesNotExist:
            return Response({"detail": "Faculty profile not found."}, status=404)
        except Exception as e:
            print(f"ERROR in FacultyStudentProfileAPIView: {str(e)}")
            return Response({"detail": f"Error: {str(e)}"}, status=500)


class FacultySendFeedbackAPIView(APIView):
    """
    POST /api/progress/faculty/feedback/send/
    Allows faculty to send feedback/notes to students they teach.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Ensure user is faculty
        if getattr(user, "role_type", "") != "faculty":
            return Response({"detail": "Forbidden. Faculty access only."}, status=403)
        
        try:
            print(f"DEBUG [Backend-FacultySendFeedback]: User: {user.username}")
            print(f"DEBUG [Backend-FacultySendFeedback]: Request data: {request.data}")
            
            student_id = request.data.get("student")
            grade_id = request.data.get("grade")
            message = request.data.get("message", "").strip()
            
            print(f"DEBUG [Backend-FacultySendFeedback]: Parsed - student_id={student_id}, grade_id={grade_id}, message='{message}'")
            
            if not student_id:
                error_msg = "Student ID is required."
                print(f"DEBUG [Backend-FacultySendFeedback]: {error_msg}")
                return Response({"detail": error_msg}, status=400)
            
            if not message:
                error_msg = "Message cannot be empty."
                print(f"DEBUG [Backend-FacultySendFeedback]: {error_msg}")
                return Response({"detail": error_msg}, status=400)
            
            # Get student
            print(f"DEBUG [Backend-FacultySendFeedback]: Searching for student with identifier: '{student_id}'")
            
            try:
                # Try institutional_id first
                student_profile = StudentProfile.objects.select_related("user").get(
                    user__institutional_id=student_id
                )
                print(f"DEBUG [Backend-FacultySendFeedback]: Found by institutional_id: {student_id}")
            except StudentProfile.DoesNotExist:
                try:
                    # Try username
                    student_profile = StudentProfile.objects.select_related("user").get(
                        user__username=student_id
                    )
                    print(f"DEBUG [Backend-FacultySendFeedback]: Found by username: {student_id}")
                except StudentProfile.DoesNotExist:
                    try:
                        # Try user ID if it's numeric
                        if student_id.isdigit():
                            student_profile = StudentProfile.objects.select_related("user").get(
                                user__id=int(student_id)
                            )
                            print(f"DEBUG [Backend-FacultySendFeedback]: Found by user ID: {student_id}")
                        else:
                            error_msg = f"Student not found with identifier: {student_id}"
                            print(f"DEBUG [Backend-FacultySendFeedback]: {error_msg}")
                            return Response({"detail": error_msg}, status=404)
                    except (StudentProfile.DoesNotExist, ValueError):
                        error_msg = f"Student not found with identifier: {student_id}"
                        print(f"DEBUG [Backend-FacultySendFeedback]: {error_msg}")
                        return Response({"detail": error_msg}, status=404)
            
            student_user = student_profile.user
            print(f"DEBUG [Backend-FacultySendFeedback]: Student found - Username: {student_user.username}, ID: {student_user.id}, Institutional ID: {student_user.institutional_id}")
            
            # Check if faculty teaches this student
            try:
                faculty_profile = FacultyProfile.objects.get(user=user)
            except FacultyProfile.DoesNotExist:
                error_msg = "Faculty profile not found."
                print(f"DEBUG [Backend-FacultySendFeedback]: {error_msg}")
                return Response({"detail": error_msg}, status=404)
            
            teaches_student = Class.objects.filter(
                faculty=faculty_profile,
                enrollments__student=student_profile
            ).exists()
            
            if not teaches_student:
                error_msg = f"You don't teach this student."
                print(f"DEBUG [Backend-FacultySendFeedback]: {error_msg}")
                return Response({"detail": error_msg}, status=403)
            
            # Validate grade_id if provided
            grade = None
            if grade_id:
                try:
                    print(f"DEBUG [Backend-FacultySendFeedback]: Looking for grade with ID: {grade_id}")
                    grade = FinalGrade.objects.get(
                        grade_id=grade_id,
                        student=student_user
                    )
                    print(f"DEBUG [Backend-FacultySendFeedback]: Found grade: {grade_id} for course: {grade.course.code if grade.course else 'Unknown'}")
                    
                    # Verify faculty teaches this course
                    teaches_course = Class.objects.filter(
                        faculty=faculty_profile,
                        course=grade.course,
                        enrollments__student=student_profile
                    ).exists()
                    
                    if not teaches_course:
                        error_msg = "You don't teach this course to the student."
                        print(f"DEBUG [Backend-FacultySendFeedback]: {error_msg}")
                        return Response({"detail": error_msg}, status=403)
                except FinalGrade.DoesNotExist:
                    error_msg = f"Invalid grade ID: {grade_id}"
                    print(f"DEBUG [Backend-FacultySendFeedback]: {error_msg}")
                    return Response({"detail": error_msg}, status=400)
            else:
                print(f"DEBUG [Backend-FacultySendFeedback]: No grade ID provided, sending general feedback")
            
            # Create the feedback message
            print(f"DEBUG [Backend-FacultySendFeedback]: Creating FacultyFeedbackMessage...")
            try:
                feedback = FacultyFeedbackMessage.objects.create(
                    student=student_user,
                    faculty=user,
                    grade=grade,  # This can be None now
                    message=message,
                    status="unread"
                )
                print(f"DEBUG [Backend-FacultySendFeedback]: Message created with ID: {feedback.id}")
            except Exception as e:
                error_msg = f"Failed to create feedback message: {str(e)}"
                print(f"DEBUG [Backend-FacultySendFeedback]: {error_msg}")
                import traceback
                traceback.print_exc()
                return Response({"detail": error_msg}, status=500)
            
            # Return the created message
            try:
                serializer = FacultyFeedbackMessageSerializer(feedback)
                print(f"DEBUG [Backend-FacultySendFeedback]: Returning success response")
                return Response(serializer.data, status=201)
            except Exception as e:
                error_msg = f"Failed to serialize response: {str(e)}"
                print(f"DEBUG [Backend-FacultySendFeedback]: {error_msg}")
                return Response({"detail": error_msg}, status=500)
            
        except Exception as e:
            error_msg = f"Server error: {str(e)}"
            print(f"ERROR in FacultySendFeedbackAPIView: {error_msg}")
            import traceback
            traceback.print_exc()
            return Response({"detail": error_msg}, status=500)


class FacultyNotesListAPIView(APIView):
    """
    GET /api/progress/faculty/notes/
    Returns all notes sent by the faculty (to any student).
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Ensure user is faculty
        if getattr(user, "role_type", "") != "faculty":
            return Response({"detail": "Forbidden. Faculty access only."}, status=403)
        
        # Get all notes sent by this faculty
        notes = FacultyFeedbackMessage.objects.filter(
            faculty=user
        ).select_related("student", "grade", "grade__course").order_by("-date_sent")
        
        notes_data = []
        for note in notes:
            notes_data.append({
                "id": note.id,
                "student": note.student.id,
                "student_name": note.student.get_full_name(),
                "student_id": note.student.institutional_id or note.student.username,
                "grade": note.grade.grade_id if note.grade else None,
                "subject": note.grade.course.code if note.grade and note.grade.course else "General Feedback",
                "message": note.message,
                "date_sent": note.date_sent.isoformat(),
                "date": note.date_sent.strftime("%b %d, %Y"),
                "status": note.status,
            })
        
        return Response(notes_data, status=200)