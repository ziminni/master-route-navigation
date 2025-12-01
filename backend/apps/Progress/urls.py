# backend/apps/Progress/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    FacultySendSingleNoteAPIView,
    StudentFeedbackListAPIView,
    MarkMessageReadAPIView,
    DeleteMessageAPIView,
)

from .views_admin import (
    AdminSectionsAPIView,
    AdminSectionStudentsAPIView,
    AdminStudentProfileAPIView,
)

from .views_faculty import (
    FacultySectionsAPIView,
    FacultySectionStudentsAPIView,
    FacultyStudentProfileAPIView,
    FacultySendFeedbackAPIView,
    FacultyNotesListAPIView,
)

from . import views_student

router = DefaultRouter()

urlpatterns = [
    # ---- Student Messages / Faculty Feedback ----
    path("student/messages/", StudentFeedbackListAPIView.as_view(), name="student-messages"),
    path("student/messages/<int:pk>/read/", MarkMessageReadAPIView.as_view(), name="student-message-read"),
    path("student/messages/<int:pk>/delete/", DeleteMessageAPIView.as_view(), name="student-message-delete"),

    # ---- Student Grades / Subjects / Degree Progress ----
    path("student/grades/", views_student.StudentGradesAPIView.as_view(), name="student-grades"),
    path("student/subjects/", views_student.StudentSubjectsAPIView.as_view(), name="student-subjects"),
    path("student/degreeprogress/", views_student.StudentDegreeProgressAPIView.as_view(), name="student-degreeprogress"),
    path("student/gwa/", views_student.StudentGWAAPIView.as_view(), name="student-gwa"),

    # ---- Faculty Notes ----
    path("student/latest-note/", views_student.StudentLatestNoteAPIView.as_view(), name="student-latest-note"),
    path("student/post-note/", FacultySendSingleNoteAPIView.as_view(), name="student-post-note"),

    # ---- Faculty Feedback / Grade Updates ----
    # Use the faculty-specific view (from views_faculty.py)
    path("faculty/feedback/send/", FacultySendFeedbackAPIView.as_view(), name="faculty-feedback-send"),

    # ---- Faculty Endpoints ----
    path("faculty/sections/", FacultySectionsAPIView.as_view(), name="faculty-sections"),
    path("faculty/section/<str:section_name>/students/", FacultySectionStudentsAPIView.as_view(), name="faculty-section-students"),
    path("faculty/student/<str:student_id>/profile/", FacultyStudentProfileAPIView.as_view(), name="faculty-student-profile"),
    path("faculty/notes/", FacultyNotesListAPIView.as_view(), name="faculty-notes"),

    # ---- Admin Endpoints ----
    path("admin/sections/", AdminSectionsAPIView.as_view(), name="admin-sections"),
    path("admin/section/<str:section_name>/students/", AdminSectionStudentsAPIView.as_view()),
    path("admin/student/<str:student_id>/profile/", AdminStudentProfileAPIView.as_view()),

    path('', include(router.urls)),
]