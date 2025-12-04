from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,permissions, viewsets, filters
from django.contrib.auth import authenticate,get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from .serializers import (
    BaseUserSerializer, LoginSerializer
)
from rest_framework.decorators import action

from rest_framework.parsers import MultiPartParser, FormParser
from .models import BaseUser
from PIL import Image

# Create your views here.

User = get_user_model()

# Convert to dictionary
ROLE_PRIORITY = ["admin", "faculty", "staff", "student"] 
'''
    choices = {
1:'ADMIN',
2:'STUDENT'
}


user.choices(choices)

serilazer

role.charfield(choices.data)

'''
class UserLoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)          # raises 400/401 on error
        data = ser.validated_data

        # accept either a user object or an id from the serializer
        user = data.pop("user", None)
        if user is None:
            user = User.objects.get(id=data.pop("user_id"))

        access = data.get("access") or data.get("access_token")
        payload = {
            "message": "Login successful",
            "access": access,                       # new key
            "access_token": access,                 # backward-compat
            "refresh": data.get("refresh"),
            "roles": data.get("roles", []),
            "primary_role": data.get("primary_role"),
            "user": BaseUserSerializer(user).data,
        }
        return Response(payload, status=status.HTTP_200_OK)


class UserProfileAPIView(APIView):
    
    # Handles fetching and updating the user profile.
    # This requires the user to be authenticated.
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile_data = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        return Response(profile_data, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.save()

        return Response({'message': 'Profile updated successfully'}, status=status.HTTP_200_OK)

class UserRegistrationAPIView(APIView):
    """
    Handles user registration (creating a new user).
    """
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')

        if not username or not password or not email:
            return Response({"message": "Username, password, and email are required."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"message": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"message": "Email is already registered."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)

        return Response({
            "message": "User created successfully",
            "username": user.username,
            "email": user.email
        }, status=status.HTTP_201_CREATED)
    
# Method na admin ra makagamit or some sort
from .services import OrgOfficer, Registrar

User = get_user_model()

class PromoteToOfficerAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_id):
        user = User.objects.get(pk=user_id)
        OrgOfficer.grant(user)
        return Response({"message": "User promoted to org_officer"}, status=200)

class DemoteOfficerAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_id):
        user = User.objects.get(pk=user_id)
        OrgOfficer.revoke(user)
        return Response({"message": "User removed from org_officer"}, status=200)
    
class PromoteRegistrarAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def post(self, request, user_id):
        user= User.objects.get(pk=user_id)
        Registrar.grant(user)
        return Response({"message": "User promoted to Registrar"}, status=200)
class DemoteRegistrarAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def post(self, request, user_id):
        user= User.objects.get(pk=user_id)
        Registrar.revoke(user)
        return Response({"message": "User retired from Registrar"}, status=200)
    
from .serializers import AdminUserListSerializer
# class UserViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = User.objects.all().order_by("id")
#     serializer_class = AdminUserListSerializer
#     permission_classes = [permissions.IsAuthenticated]
#     filter_backends = [filters.SearchFilter, filters.OrderingFilter]
#     search_fields = ["username", "email", "first_name", "last_name"]
#     ordering_fields = ["id", "username", "email", "first_name", "last_name"]

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .serializers import BaseUserSerializer

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = BaseUserSerializer(request.user, context={"request": request}).data
        return Response(data, status=status.HTTP_200_OK)

# For the resume builder shit
from rest_framework import viewsets, permissions
from .models import Education, Experience, Skill, Interest
from .serializers import (
    EducationSerializer, ExperienceSerializer, SkillSerializer, InterestSerializer
)

class _OwnedMixin:
    permission_classes = [permissions.IsAuthenticated]
    model = None
    serializer_class = None
    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user).order_by("-created_at")
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class EducationViewSet(_OwnedMixin, viewsets.ModelViewSet):
    model = Education
    serializer_class = EducationSerializer

class ExperienceViewSet(_OwnedMixin, viewsets.ModelViewSet):
    model = Experience
    serializer_class = ExperienceSerializer

class SkillViewSet(_OwnedMixin, viewsets.ModelViewSet):
    model = Skill
    serializer_class = SkillSerializer

class InterestViewSet(_OwnedMixin, viewsets.ModelViewSet):
    model = Interest
    serializer_class = InterestSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = BaseUser.objects.all().order_by("id")
    serializer_class = AdminUserListSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(
        detail=False, methods=["post"], url_path="avatar",
        parser_classes=[MultiPartParser, FormParser],
        permission_classes=[permissions.IsAuthenticated],
    )
    def upload_avatar(self, request):
        f = request.data.get("file")
        if not f:
            return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # 10 MB limit (keep message consistent)
        if f.size and f.size > 10 * 1024 * 1024:
            return Response({"detail": "Max 10MB."}, status=status.HTTP_400_BAD_REQUEST)

        allowed_ct = {"image/jpeg", "image/png"}
        allowed_ext = {".jpg", ".jpeg", ".png"}
        name_lower = (getattr(f, "name", "") or "").lower()
        ct_ok = (getattr(f, "content_type", None) in allowed_ct)
        ext_ok = any(name_lower.endswith(ext) for ext in allowed_ext)
        if not (ct_ok or ext_ok):
            return Response({"detail": "JPEG/PNG only."}, status=status.HTTP_400_BAD_REQUEST)

        # verify image content
        pos = f.tell()
        try:
            Image.open(f).verify()
        except Exception:
            return Response({"detail": "Invalid image file."}, status=status.HTTP_400_BAD_REQUEST)
        finally:
            f.seek(pos)

        user = request.user
        old_name = user.profile_picture.name if user.profile_picture else None

        user.profile_picture = f
        user.save(update_fields=["profile_picture"])

        # remove old file after successful save
        if old_name:
            try:
                user.profile_picture.storage.delete(old_name)
            except Exception:
                pass

        abs_url = request.build_absolute_uri(user.profile_picture.url)
        return Response({"avatar_url": abs_url, "path": user.profile_picture.name}, status=status.HTTP_200_OK)

# For password recovery (views.py)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
import secrets
from .models import PasswordReset

User = get_user_model()

GENERIC_OK = Response({"message":"If the email exists, an OTP was sent."}, status=200)

class PasswordOTPRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "password_reset"  # add DRF throttling

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        if not email:
            return Response({"detail":"Email required."}, status=400)
        try:
            user = User.objects.get(email__iexact=email, is_active=True)
        except User.DoesNotExist:
            return GENERIC_OK  # do not leak account existence

        # create + email OTP
        pr, otp = PasswordReset.create_for(user)
        send_mail(
            subject="Your CISC password reset code",
            message=f"Your code is: {otp} (valid for 10 minutes)",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[email],
            fail_silently=True,
        )
        return GENERIC_OK

class PasswordOTPVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        otp   = (request.data.get("otp")   or "").strip()
        if not email or not otp:
            return Response({"detail":"Email and OTP required."}, status=400)
        try:
            user = User.objects.get(email__iexact=email, is_active=True)
        except User.DoesNotExist:
            return Response({"detail":"Invalid OTP."}, status=400)

        pr = (PasswordReset.objects
              .filter(user=user, verified=False, expires_at__gte=timezone.now())
              .order_by("-id").first())
        if not pr:
            return Response({"detail":"OTP expired or not found."}, status=400)

        if pr.attempts >= 5:
            return Response({"detail":"Too many attempts."}, status=429)

        pr.attempts += 1
        if PasswordReset.hash(otp) != pr.code_hash:
            pr.save(update_fields=["attempts"])
            return Response({"detail":"Invalid OTP."}, status=400)

        # success → issue a short-lived one-time reset token
        pr.verified = True
        pr.reset_token = secrets.token_urlsafe(32)
        pr.save(update_fields=["verified", "reset_token", "attempts"])
        return Response({"reset_token": pr.reset_token}, status=200)

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token") or ""
        newpw = request.data.get("new_password") or ""
        if len(newpw) < 6:
            return Response({"detail":"Password too short."}, status=400)

        pr = PasswordReset.objects.filter(reset_token=token, verified=True).first()
        if not pr or pr.expires_at < timezone.now():
            return Response({"detail":"Invalid or expired token."}, status=400)

        user = pr.user
        user.set_password(newpw)
        user.save(update_fields=["password"])

        # invalidate token
        pr.delete()
        return Response({"message":"Password changed."}, status=200)