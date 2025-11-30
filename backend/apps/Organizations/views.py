from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from .models import EventType, EventSchedule, Event, EventScheduleBlock, EventAttendance, EventApproval
from .serializers import *
from apps.Users.models import StudentProfile, FacultyProfile

# Custom Permissions
class IsOrgOfficer(permissions.BasePermission):
    """Check if user has org_officer role in their StudentProfile"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'student_profile') and
            'org_officer' in request.user.groups.values_list('name', flat=True)
        )

class IsFaculty(permissions.BasePermission):
    """Check if user has FacultyProfile"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'faculty_profile')
        )

class IsStudent(permissions.BasePermission):
    """Check if user has StudentProfile"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'student_profile')
        )

class CanApproveEvents(permissions.BasePermission):
    """Check if user can approve events (Faculty)"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'faculty_profile')
        )

# Viewsets
class EventTypeViewSet(viewsets.ModelViewSet):
    queryset = EventType.objects.all()
    serializer_class = EventTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

class EventScheduleBlockViewSet(viewsets.ModelViewSet):
    queryset = EventScheduleBlock.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EventScheduleBlockDetailSerializer
        return EventScheduleBlockSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOrgOfficer()]
        return [permissions.IsAuthenticated()]

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EventDetailSerializer
        elif self.action == 'update_status':
            return EventStatusUpdateSerializer
        elif self.action == 'create':
            return EventCreateSerializer
        return EventSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [permissions.IsAuthenticated(), IsOrgOfficer()]
        elif self.action in ['update_status', 'approve', 'reject', 'reschedule']:
            return [permissions.IsAuthenticated(), CanApproveEvents()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Students can only see approved, current, and upcoming events
        if hasattr(self.request.user, 'student_profile'):
            # Filter for approved events that are either current or upcoming
            current_date = timezone.now().date()
            return queryset.filter(
                event_status=Event.EventStatus.approved
            ).prefetch_related('eventschedule_set')
        
        # Faculty can see all events including proposed ones
        elif hasattr(self.request.user, 'faculty_profile'):
            return queryset.all()
        
        # Org officers can see all events they created
        elif (hasattr(self.request.user, 'student_profile') and 
              'org_officer' in self.request.user.groups.values_list('name', flat=True)):
            # Get events created by this org officer through event schedules
            org_officer_schedules = EventSchedule.objects.filter(
                user_id=self.request.user.student_profile
            )
            event_ids = org_officer_schedules.values_list('event_id', flat=True)
            return queryset.filter(id__in=event_ids)
        
        return queryset.none()
    
    def perform_create(self, serializer):
        # Auto-set the semester to current active semester if available
        # You might want to modify this logic based on your semester system
        from apps.Academics.models import Semester
        current_semester = Semester.objects.filter(is_active=True).first()
        
        event = serializer.save(sem_id=current_semester)
        
        # Create initial event schedule for the org officer
        if hasattr(self.request.user, 'student_profile'):
            EventSchedule.objects.create(
                event_schedule_block_id=event.event_schedule_block,
                event_id=event,
                user_id=self.request.user.student_profile,
                start_time=timezone.now().time(),
                end_time=(timezone.now() + timezone.timedelta(hours=2)).time(),
                creation_date=timezone.now()
            )
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update event status (used by faculty)"""
        event = self.get_object()
        serializer = self.get_serializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an event and create approval record"""
        event = self.get_object()
        
        if event.event_status != Event.EventStatus.proposed:
            return Response(
                {"error": "Only proposed events can be approved"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create approval record
        approval = EventApproval.objects.create(
            event_id=event,
            approver_id=request.user.faculty_profile,
            notes=request.data.get('notes', '')
        )
        
        # Update event status
        event.event_status = Event.EventStatus.approved
        event.save()
        
        return Response(
            EventApprovalSerializer(approval).data, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject an event"""
        event = self.get_object()
        
        if event.event_status != Event.EventStatus.proposed:
            return Response(
                {"error": "Only proposed events can be rejected"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # You might want to create a rejection record or just update status
        event.event_status = "rejected"  # You might want to add this to EventStatus
        event.save()
        
        return Response(
            {"message": "Event rejected successfully"}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def current_upcoming(self, request):
        """Get current and upcoming events for students"""
        if not hasattr(request.user, 'student_profile'):
            return Response(
                {"error": "Only students can access this endpoint"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        current_time = timezone.now()
        
        # Get approved events with schedules in the future or ongoing
        current_upcoming_events = Event.objects.filter(
            event_status=Event.EventStatus.approved,
            eventschedule__start_time__gte=current_time.time()
        ).distinct()
        
        serializer = EventSerializer(current_upcoming_events, many=True)
        return Response(serializer.data)

class EventScheduleViewSet(viewsets.ModelViewSet):
    queryset = EventSchedule.objects.all()
    serializer_class = EventScheduleSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOrgOfficer()]
        return [permissions.IsAuthenticated()]

class EventAttendanceViewSet(viewsets.ModelViewSet):
    queryset = EventAttendance.objects.all()
    serializer_class = EventAttendanceSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsStudent()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Students can only see their own attendance
        if hasattr(self.request.user, 'student_profile'):
            return queryset.filter(student_id=self.request.user.student_profile)
        
        # Faculty and org officers can see all attendance
        return queryset
    
    def perform_create(self, serializer):
        # Ensure student can only create attendance for themselves
        if hasattr(self.request.user, 'student_profile'):
            serializer.save(student_id=self.request.user.student_profile)

class EventApprovalViewSet(viewsets.ModelViewSet):
    queryset = EventApproval.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EventApprovalCreateSerializer
        return EventApprovalSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), CanApproveEvents()]
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        # Auto-set the approver to the current faculty user
        if hasattr(self.request.user, 'faculty_profile'):
            serializer.save(approver_id=self.request.user.faculty_profile)

# Additional serializers for specialized operations
class EventCreateSerializer(serializers.ModelSerializer):
    """Serializer specifically for org officers creating events"""
    class Meta:
        model = Event
        fields = ['event_schedule_block', 'event_type', 'title', 'venue', 'sem_id']
    
    def validate(self, data):
        # Ensure org officers can only create events in proposed status
        data['event_status'] = Event.EventStatus.proposed
        return data