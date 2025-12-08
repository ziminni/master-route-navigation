from django.urls import path
from .views import FeedbackCreateAPIView, FeedbackListAPIView

urlpatterns = [
    path("", FeedbackCreateAPIView.as_view(), name="feedback-create"),
    path("list/", FeedbackListAPIView.as_view(), name="feedback-list"),
]
