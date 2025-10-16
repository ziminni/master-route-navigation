from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import BaseUser
from rest_framework.exceptions import AuthenticationFailed

# serializers.py
from rest_framework import serializers
from django.conf import settings
from .models import (
    BaseUser, FacultyDepartment, Position, Program, Section,
    FacultyProfile, StudentProfile, StaffProfile
)
User=get_user_model()

class FacultyDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacultyDepartment
        fields = ["id", "department_name"]

class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ["id", "position_name"]

class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = ["id", "program_name"]

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ["id", "section_name"]

class BaseUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseUser
        fields = [
            "id", "username", "email",
            "first_name", "middle_name", "last_name", "suffix",
            "profile_picture", "birth_date",
            "institutional_id", "phone_number",
            "role_type",
        ]
        read_only_fields = ["id", "institutional_id", "username", "email"]

class FacultyProfileSerializer(serializers.ModelSerializer):
    user = BaseUserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=BaseUser.objects.all(),
        write_only=True,
        source="user"
    )
    faculty_department_detail = FacultyDepartmentSerializer(source="faculty_department", read_only=True)
    position_detail = PositionSerializer(source="position", read_only=True)

    class Meta:
        model = FacultyProfile
        fields = [
            "user", "user_id",
            "faculty_department", "faculty_department_detail",
            "position", "position_detail",
            "hire_date",
        ]


class StudentProfileSerializer(serializers.ModelSerializer):
    user = BaseUserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=BaseUser.objects.all(),
        write_only=True,
        source="user"
    )
    program_detail = ProgramSerializer(source="program", read_only=True)
    section_detail = SectionSerializer(source="section", read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "user", "user_id",
            "program", "program_detail",
            "section", "section_detail",
            "indiv_points", "year_level",
        ]


class StaffProfileSerializer(serializers.ModelSerializer):
    user = BaseUserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=BaseUser.objects.all(),
        write_only=True,
        source="user"
    )
    faculty_department_detail = FacultyDepartmentSerializer(source="faculty_department", read_only=True)

    class Meta:
        model = StaffProfile
        fields = [
            "user", "user_id",
            "faculty_department", "faculty_department_detail",
            "job_title",
        ]
        
class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = (attrs.get("identifier") or "").strip()
        password   = attrs.get("password") or ""

        if not identifier or not password:
            raise AuthenticationFailed("Missing credentials.")

        # resolve account by email or username
        user_obj = None
        if "@" in identifier:
            try:
                user_obj = User.objects.get(email__iexact=identifier)
            except User.DoesNotExist:
                user_obj = None
        if user_obj is None:
            try:
                user_obj = User.objects.get(username=identifier)
            except User.DoesNotExist:
                user_obj = None

        if user_obj is None:
            # secure alternative: raise AuthenticationFailed("Invalid username or password.")
            raise AuthenticationFailed("Account not found.")

        user = authenticate(username=user_obj.username, password=password)
        if user is None:
            # secure alternative: raise AuthenticationFailed("Invalid username or password.")
            raise AuthenticationFailed("Incorrect password.")

        if not user.is_active:
            raise AuthenticationFailed("Account is inactive.")

        refresh = RefreshToken.for_user(user)
        roles = list(user.groups.values_list("name", flat=True))

        ROLE_PRIORITY = ["admin", "faculty", "staff", "student"]
        primary_role = next((r for r in ROLE_PRIORITY if r in roles), None) or getattr(user, "primary_role", None)

        return {
            "access": str(refresh.access_token),
            "access_token": str(refresh.access_token),
            "refresh": str(refresh),
            "roles": roles,
            "primary_role": primary_role,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
        }

    # def validate(self, attrs):
    #     identifier = attrs.get("identifier")
    #     password = attrs.get("password")
    #     user = authenticate(username=identifier, password=password)
    #     roles = list(user.groups.values_list("name", flat=True))

    #     if user is None and "@" in identifier:
    #         try:
    #             u = User.objects.get(email__iexact=identifier)
    #             user = authenticate(username=u.username, password=password)
    #         except User.DoesNotExist:
    #             pass

    #     if user is None:
    #         raise serializers.ValidationError("Invalid credentials.")
    #     if not user.is_active:
    #         raise serializers.ValidationError("Account is inactive.")

    #     refresh = RefreshToken.for_user(user)
    #     roles = list(user.groups.values_list("name", flat=True))

    #     # Implement custom permissions
    #     ROLE_PRIORITY = ["admin", "faculty", "staff", "student"]
    #     primary_role = next((r for r in ROLE_PRIORITY if r in roles), None)

    #     return {
    #         "user": user,
    #         "access_token": str(refresh.access_token),
    #         "roles": roles,
    #         "primary_role": primary_role,
    #     }
    

class AdminUserListSerializer(serializers.ModelSerializer):
    # show group names as a comma-join-friendly list
    groups = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )

    class Meta:
        model = User
        fields = [
            "id", "username", "email",
            "first_name", "last_name",
            "is_active", "is_staff", "is_superuser",
            "groups",
        ]

class BaseUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    primary_role = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    student_profile = StudentProfileSerializer(read_only=True)
    faculty_profile = FacultyProfileSerializer(read_only=True)
    staff_profile   = StaffProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id", "username", "email",
            "first_name", "middle_name", "last_name", "full_name",
            "institutional_id", "phone_number", "birth_date",
            "primary_role", "roles", "profile_picture",
            "student_profile", "faculty_profile", "staff_profile",
        )

    def get_full_name(self, obj):
        parts = [obj.first_name, getattr(obj, "middle_name", None), obj.last_name]
        return " ".join(p for p in parts if p).strip() or obj.username

    def _roles_list(self, obj):
        # Combine role_type with Django groups
        groups = list(obj.groups.values_list("name", flat=True))
        role_type = getattr(obj, "role_type", None)
        if role_type and role_type not in groups:
            groups.insert(0, role_type)
        return groups

    def get_roles(self, obj):
        return self._roles_list(obj)

    def get_primary_role(self, obj):
        priority = ["admin", "faculty", "staff", "student"]
        roles = self._roles_list(obj)
        for r in priority:
            if r in roles:
                return r
        # fallback to role_type if none matched
        return getattr(obj, "role_type", None)

    def get_profile_picture(self, obj):
        if getattr(obj, "profile_picture", None) and obj.profile_picture:
            try:
                url = obj.profile_picture.url
            except Exception:
                return None
            req = self.context.get("request")
            return req.build_absolute_uri(url) if req else url
        return None
    

# Serializers for the simple resume elements models
from rest_framework import serializers
from .models import Education, Experience, Skill, Interest

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = "__all__"
        read_only_fields = ("user","created_at","updated_at")

class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = "__all__"
        read_only_fields = ("user","created_at","updated_at")

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = "__all__"
        read_only_fields = ("user","created_at","updated_at")

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = "__all__"
        read_only_fields = ("user","created_at","updated_at")