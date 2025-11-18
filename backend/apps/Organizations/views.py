from django.utils import timezone 
from django.shortcuts import render

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from Users.models import FacultyProfile, StudentProfile
from Organizations.models import EventType, EventSchedule, Event, EventScheduleBlock, EventAttendance, EventApproval
from Organizations.serializer import (
    EventTypeSerializer, EventScheduleSerializer, EventSerializer,
    EventScheduleBlockSerializer, EventAttendanceSerializer, EventApprovalSerializer
)

class EventTypeViewSet(viewsets.ModelViewSet):
    queryset = EventType.objects.all()
    serializer_class = EventTypeSerializer

class EventScheduleBlockViewSet(viewsets.ModelViewSet):
    queryset = EventScheduleBlock.objects.all()
    serializer_class = EventScheduleBlockSerializer

class EventScheduleViewSet(viewsets.ModelViewSet):
    queryset = EventSchedule.objects.all()
    serializer_class = EventScheduleSerializer
    
    def perform_create(self, serializer):
        serializer.save(creation_date=timezone.now())

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    
    @action(detail=True, methods=['post'])
    def approve_event(self, request, pk=None):
        event = self.get_object()
        approver_id = request.data.get('approver_id')
        notes = request.data.get('notes', '')
        
        if not approver_id:
            return Response(
                {'error': 'approver_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check if approver exists
            approver = FacultyProfile.objects.get(id=approver_id)
            
            # Check if already approved
            if EventApproval.objects.filter(event_id=event).exists():
                return Response(
                    {'error': 'Event is already approved'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create approval
            approval = EventApproval.objects.create(
                event_id=event,
                approver_id=approver,  # Use the object, not approver_id_id
                notes=notes
            )
            
            # Update event status
            event.event_status = Event.EventStatus.approved
            event.save()
            
            serializer = EventApprovalSerializer(approval)
            return Response(serializer.data)
            
        except FacultyProfile.DoesNotExist:
            return Response(
                {'error': 'Approver not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def attendance(self, request, pk=None):
        """Get attendance records for this event"""
        event = self.get_object()
        attendance = EventAttendance.objects.filter(event_id=event)
        serializer = EventAttendanceSerializer(attendance, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update event status"""
        event = self.get_object()
        new_status = request.data.get('event_status')
        
        if new_status not in dict(Event.EventStatus.choices):
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event.event_status = new_status
        event.save()
        
        serializer = EventSerializer(event)
        return Response(serializer.data)

class EventAttendanceViewSet(viewsets.ModelViewSet):
    queryset = EventAttendance.objects.all()
    serializer_class = EventAttendanceSerializer
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """Get attendance records by student"""
        student_id = request.query_params.get('student_id')
        if student_id:
            attendance = EventAttendance.objects.filter(student_id=student_id)
            serializer = self.get_serializer(attendance, many=True)
            return Response(serializer.data)
        return Response(
            {'error': 'student_id parameter is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def by_event(self, request):
        """Get attendance records by event"""
        event_id = request.query_params.get('event_id')
        if event_id:
            attendance = EventAttendance.objects.filter(event_id=event_id)
            serializer = self.get_serializer(attendance, many=True)
            return Response(serializer.data)
        return Response(
            {'error': 'event_id parameter is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

class EventApprovalViewSet(viewsets.ModelViewSet):
    queryset = EventApproval.objects.all()
    serializer_class = EventApprovalSerializer
    
    def create(self, request, *args, **kwargs):
        """Override create to handle the unique constraint"""
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            if 'events_approved_only_once' in str(e):
                return Response(
                    {'error': 'Event can only be approved once'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            raise e