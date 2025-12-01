# backend/apps/Progress/grades_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.Progress.models import FinalGrade
from apps.Users.models import StudentProfile


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_grades(request):
    user = request.user

    try:
        student_profile = StudentProfile.objects.get(user=user)
    except StudentProfile.DoesNotExist:
        return Response({"detail": "Student profile not found", "academic_years": []}, status=200)

    grades = FinalGrade.objects.filter(student=student_profile.user).select_related('course', 'semester')

    academic_map = {}

    for g in grades:
        # Use semester's academic_year and term fields
        sy = getattr(g.semester, "academic_year", "N/A")
        sem = getattr(g.semester, "term", "N/A")

        if sy not in academic_map:
            academic_map[sy] = {}

        if sem not in academic_map[sy]:
            academic_map[sy][sem] = []

        academic_map[sy][sem].append({
            "course_code": getattr(g.course, "code", ""),
            "course_title": getattr(g.course, "title", ""),
            "final_grade": g.final_grade,
            "remarks": getattr(g, "status", ""),
        })

    formatted = {
        "academic_years": [
            {
                "school_year": sy,
                "semesters": [
                    {
                        "name": sem,
                        "courses": academic_map[sy][sem]
                    }
                    for sem in academic_map[sy]
                ]
            }
            for sy in academic_map
        ]
    }

    return Response(formatted, status=200)