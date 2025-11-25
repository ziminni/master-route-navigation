from django.urls import path
from .views import (
    FacultySendFeedbackAPIView,
    StudentFeedbackListAPIView,
    MarkMessageReadAPIView,
)

urlpatterns = [
    path("faculty/send/", FacultySendFeedbackAPIView.as_view()),
    path("student/messages/", StudentFeedbackListAPIView.as_view()),
    path("student/messages/<int:pk>/read/", MarkMessageReadAPIView.as_view()),
]