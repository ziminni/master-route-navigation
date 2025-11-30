from django.forms import ValidationError
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from datetime import datetime, timedelta, time
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.utils.timezone import make_aware
from .models import AvailabilityRule, BusyBlock, Appointment
from .serializers import FacultyProfileListSerializer, AvailabilityRuleSerializer, AvailableSlotSerializer, AppointmentCreateSerializer, AppointmentListSerializer, AppointmentUpdateSerializer
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_datetime
from apps.Users.models import FacultyProfile


class AvailabilityRuleCreateView(generics.CreateAPIView):
    queryset = AvailabilityRule.objects.all()
    serializer_class = AvailabilityRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        # Faculty should not manually set faculty_id
        if user.role_type == "faculty":
            serializer.save(faculty=user.faculty_profile)
        else:
            raise PermissionDenied("Only faculty can create availability rules.")

class FacultyAvailableScheduleView(generics.ListAPIView):
    """
    Returns FINAL AVAILABLE SLOTS based on:
    - AvailabilityRule (base schedule)
    - BusyBlock (overrides)
    - Appointments (if applicable)
    
    """
    serializer_class = AvailableSlotSerializer

    def get_queryset(self):
        faculty_id = self.kwargs.get("faculty_id")
        date_str = self.kwargs.get("date")  # date format: YYYY-MM-DD

        if not faculty_id or not date_str:
            raise ValidationError("faculty_id and date are required.")

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD.")

        # Map weekday number to your DoW choices (Monday=0 → 'MON')
        dow_mapping = {0: 'MON', 1: 'TUE', 2: 'WED', 3: 'THU', 4: 'FRI', 5: 'SAT', 6: 'SUN'}
        day_of_week_num = date_obj.weekday()
        day_of_week = dow_mapping[day_of_week_num]

        # ===== 1. Get Availability Rules =====
        rules = AvailabilityRule.objects.filter(
            faculty_id=faculty_id,
            day_of_week=day_of_week
        )

        slot_list = []

        # Build all slots from rules
        for rule in rules:
            start_dt = make_aware(datetime.combine(date_obj, rule.start_time))
            end_dt = make_aware(datetime.combine(date_obj, rule.end_time))
            slot_minutes = rule.slot_minutes

            cur = start_dt
            while cur + timedelta(minutes=slot_minutes) <= end_dt:
                slot_list.append({
                    "start": cur,
                    "end": cur + timedelta(minutes=slot_minutes)
                })
                cur += timedelta(minutes=slot_minutes)

        # ===== 2. Remove Busy Blocks =====
        busy_blocks = BusyBlock.objects.filter(
            faculty_id=faculty_id,
            start_at__date=date_obj  # Fixed field name
        )

        filtered_slots = []
        for slot in slot_list:
            overlapped = False
            for block in busy_blocks:
                if not (slot["end"] <= block.start_at or slot["start"] >= block.end_at):  # Fixed field names
                    overlapped = True
                    break
            if not overlapped:
                filtered_slots.append(slot)

        # ===== 3. Remove appointment bookings =====
        appointments = Appointment.objects.filter(
            faculty_id=faculty_id,
            start_at__date=date_obj  # Fixed field name
        ).exclude(status__in=[Appointment.CANCELED, Appointment.DENIED])  # Only consider active appointments

        final_slots = []
        for slot in filtered_slots:
            booked = False
            for app in appointments:
                if not (slot["end"] <= app.start_at or slot["start"] >= app.end_at):  # Fixed field names
                    booked = True
                    break
            if not booked:
                final_slots.append(slot)

        return final_slots
    
class AppointmentCreateView(generics.CreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        
        # Ensure only students can create appointments
        if not hasattr(user, 'student_profile'):
            raise PermissionDenied("Only students can create appointments.")
        
        # Auto-set the student and default status
        serializer.save(
            student=user.student_profile,
            status=Appointment.PENDING  # Always start as pending
        )

class FacultyAppointmentListView(generics.ListAPIView):
    serializer_class = AppointmentListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return appointments only for THIS faculty user."""
        faculty_profile = self.request.user.faculty_profile
        return Appointment.objects.filter(faculty=faculty_profile).order_by("-created_at")


class StudentAppointmentListView(generics.ListAPIView):
    serializer_class = AppointmentListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return appointments only for THIS student user."""
        student_profile = self.request.user.student_profile
        return Appointment.objects.filter(student=student_profile).order_by("-created_at")

class AppointmentUpdateView(generics.UpdateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_object(self):
        appointment = super().get_object()
        user = self.request.user
        
        # Check permissions based on user role
        if hasattr(user, 'faculty_profile') and appointment.faculty.user == user:
            self.allowed_actions = ['approve', 'deny', 'cancel', 'reschedule']
        elif hasattr(user, 'student_profile') and appointment.student.user == user:
            self.allowed_actions = ['cancel', 'reschedule']
        else:
            raise PermissionDenied("You cannot modify this appointment.")
        
        return appointment

    def perform_update(self, serializer):
        appointment = self.get_object()
        new_status = serializer.validated_data.get('status')
        new_start = serializer.validated_data.get('start_at')
        new_end = serializer.validated_data.get('end_at')

        # Handle status changes
        if new_status:
            self._validate_status_change(appointment, new_status)
            
        # Handle rescheduling (time changes)
        is_rescheduling = new_start or new_end
        if is_rescheduling:
            self._validate_reschedule(appointment, new_start, new_end)
            # When ANYONE reschedules, reset status to pending for faculty approval
            serializer.validated_data['status'] = Appointment.PENDING
        
        # Save the changes
        serializer.save()

    def _validate_status_change(self, appointment, new_status):
        """Validate status transitions"""
        current_status = appointment.status

        valid_transitions = {
            Appointment.PENDING: [Appointment.APPROVED, Appointment.DENIED, Appointment.CANCELED],
            Appointment.APPROVED: [Appointment.CANCELED, Appointment.COMPLETED],
            Appointment.DENIED: [Appointment.CANCELED],
            Appointment.COMPLETED: [],
            Appointment.CANCELED: [],
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise ValidationError(f"Cannot change status from {current_status} to {new_status}")
        
        if new_status == Appointment.APPROVED:
            if 'approve' not in self.allowed_actions:
                raise PermissionDenied("You cannot approve appointments.")
            self._check_conflicts(appointment)  # Only check conflicts when approving
            
        elif new_status == Appointment.DENIED:
            if 'deny' not in self.allowed_actions:
                raise PermissionDenied("You cannot deny appointments.")
                
        elif new_status == Appointment.CANCELED:
            if 'cancel' not in self.allowed_actions:
                raise PermissionDenied("You cannot cancel this appointment.")
            if current_status in [Appointment.COMPLETED, Appointment.DENIED]:
                raise ValidationError("This appointment cannot be canceled.")

    def _validate_reschedule(self, appointment, new_start, new_end):
        """Validate rescheduling"""
        if 'reschedule' not in self.allowed_actions:
            raise PermissionDenied("You cannot reschedule this appointment.")
            
        if appointment.status in [Appointment.DENIED, Appointment.COMPLETED]:
            raise ValidationError("This appointment cannot be rescheduled.")
            
        # Use existing times if not provided
        start_at = new_start if new_start else appointment.start_at
        end_at = new_end if new_end else appointment.end_at
        
        # Check for conflicts (excluding current appointment)
        conflict = Appointment.objects.filter(
            faculty=appointment.faculty,
            start_at__lt=end_at,
            end_at__gt=start_at,
            status__in=[Appointment.PENDING, Appointment.APPROVED]
        ).exclude(id=appointment.id).exists()

        if conflict:
            raise ValidationError("Time conflicts with another appointment.")

        # Check busy blocks
        busy_conflict = BusyBlock.objects.filter(
            faculty=appointment.faculty,
            start_at__lt=end_at,
            end_at__gt=start_at
        ).exists()

        if busy_conflict:
            raise ValidationError("Faculty is busy during this time.")

    def _check_conflicts(self, appointment):
        """Check conflicts for approval (same as your existing logic)"""
        conflict = Appointment.objects.filter(
            faculty=appointment.faculty,
            start_at__lt=appointment.end_at,
            end_at__gt=appointment.start_at,
            status=Appointment.APPROVED
        ).exclude(id=appointment.id).exists()

        if conflict:
            raise ValidationError("Faculty already has an approved appointment in this time.")

        busy_conflict = BusyBlock.objects.filter(
            faculty=appointment.faculty,
            start_at__lt=appointment.end_at,
            end_at__gt=appointment.start_at
        ).exists()

        if busy_conflict:
            raise ValidationError("This time slot is blocked in the faculty schedule.")



class AvailabilityRuleListView(generics.ListAPIView):
    serializer_class = AvailabilityRuleSerializer

    def get_queryset(self):
        faculty_id = self.kwargs.get("faculty_id")
        semester_id = self.kwargs.get("semester_id")
        
        # Build the queryset with filters
        queryset = AvailabilityRule.objects.all()
        
        if faculty_id:
            queryset = queryset.filter(faculty_id=faculty_id)
        
        if semester_id:
            queryset = queryset.filter(semester_id=semester_id)
            
        return queryset













class FacultyProfileListView(generics.ListAPIView):
    """
    Get all faculty profiles with their user details
    """
    queryset = FacultyProfile.objects.all()
    serializer_class = FacultyProfileListSerializer
    permission_classes = [permissions.IsAuthenticated]  # Or [permissions.AllowAny] if public

    def get_queryset(self):
        """Optionally add filtering and ordering"""
        return FacultyProfile.objects.select_related(
            'user', 
            'faculty_department',  # This is crucial!
            'position'
        ).all().order_by('user__last_name', 'user__first_name')