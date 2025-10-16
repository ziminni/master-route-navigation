from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserLoginAPIView, PromoteToOfficerAPIView, DemoteOfficerAPIView, UserViewSet, DemoteRegistrarAPIView, PromoteRegistrarAPIView, MeView, EducationViewSet, ExperienceViewSet, SkillViewSet, InterestViewSet
from .views import PasswordOTPRequestView, PasswordOTPVerifyView, PasswordResetConfirmView

router = DefaultRouter()
router.register(r"resume/education",  EducationViewSet,  basename="users-resume-education")
router.register(r"resume/experience", ExperienceViewSet, basename="users-resume-experience")
router.register(r"resume/skills",     SkillViewSet,     basename="users-resume-skills")
router.register(r"resume/interests",  InterestViewSet,  basename="users-resume-interests")
router.register(r"", UserViewSet, basename="user")

urlpatterns = [
    # Points to UserLoginAPI, to handle authentication
    path("me/", MeView.as_view(), name="users-me"),
    path('login/api/', UserLoginAPIView.as_view(), name='user-login'),
    path("roles/org-officer/<int:user_id>/promote/", PromoteToOfficerAPIView.as_view()),
    path("roles/org-officer/<int:user_id>/demote/",  DemoteOfficerAPIView.as_view()),
    path("roles/registrar/<int:user_id>/promote/", PromoteRegistrarAPIView.as_view()),
    path("roles/registrar/<int:user_id>/demote/",  DemoteRegistrarAPIView.as_view()),
    path("password/otp/request/", PasswordOTPRequestView.as_view()),
    path("password/otp/verify/",  PasswordOTPVerifyView.as_view()),
    path("password/reset/",       PasswordResetConfirmView.as_view()),
    path("", include(router.urls)),
]
