# backend/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserLoginAPIView, PromoteToOfficerAPIView, DemoteOfficerAPIView, UserViewSet, DemoteRegistrarAPIView, PromoteRegistrarAPIView

router = DefaultRouter()
router.register(r"", UserViewSet, basename="user")  # → /api/users/
urlpatterns = [
    # Points to UserLoginAPI, to handle authentication
    path("", include(router.urls)),
    path('login/api/', UserLoginAPIView.as_view(), name='user-login'),
    path("roles/org-officer/<int:user_id>/promote/", PromoteToOfficerAPIView.as_view()),
    path("roles/org-officer/<int:user_id>/demote/",  DemoteOfficerAPIView.as_view()),
    path("roles/registrar/<int:user_id>/promote/", PromoteRegistrarAPIView.as_view()),
    path("roles/registrar/<int:user_id>/demote/",  DemoteRegistrarAPIView.as_view()),
]
