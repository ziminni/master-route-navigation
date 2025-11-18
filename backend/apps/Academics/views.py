from django.shortcuts import render

# views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ScheduleBlock, ScheduleEntry
from .serializer import *

class ScheduleBlockViewSet(viewsets.ModelViewSet):
    """
    API endpoint for ScheduleBlock
    - Students: Can only access their own blocks
    - Faculty/Admin: Can access all blocks (with filtering capabilities)
     Includes nested schedule_entries with full entry details
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # ADMIN/FACULTY: Full access
        if user.is_staff or user.is_superuser or hasattr(user, 'facultyprofile'):
            queryset = ScheduleBlock.objects.all()
            
            # Allow filtering by student
            student_id = self.request.query_params.get('student_id')
            if student_id:
                queryset = queryset.filter(user_id=student_id)
                
            return queryset
            
        # STUDENT: Restricted to own data
        elif hasattr(user, 'studentprofile'):
            return ScheduleBlock.objects.filter(user_id=user.studentprofile)
        
        # DEFAULT: No access
        else:
            return ScheduleBlock.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ScheduleBlockCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ScheduleBlockUpdateSerializer
        return ScheduleBlockSerializer
    
    def perform_create(self, serializer): #This will perhaps be used when a new class is created
        user = self.request.user
        
        # Students: auto-assign their student profile. Student is VIEW ONLY. DO NOT USE THIS for student views
        if hasattr(user, 'studentprofile'):
            # serializer.save(user_id=user.studentprofile)
            pass
        # Faculty/Admin: can specify any user_id in the request
        elif user.is_staff or user.is_superuser or hasattr(user, 'facultyprofile'):
            serializer.save()
        else:
            raise serializers.ValidationError("User doesn't have appropriate permissions")
    # Above destroy method is commented out to prevent accidental deletions, not to mention it's not really usefule for a viewing intention right now lol

class ScheduleEntryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for ScheduleEntry
    - Students: Can only access entries in their own blocks
    - Faculty/Admin: Can access all entries
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # ADMIN/FACULTY: Full access
        if user.is_staff or user.is_superuser or hasattr(user, 'facultyprofile'):
            queryset = ScheduleEntry.objects.all()
            
            # Allow faculty/admin to filter by student if needed
            student_id = self.request.query_params.get('student_id')
            if student_id:
                queryset = queryset.filter(schedule_block_id__user_id=student_id)
                
            return queryset
            
        # STUDENT: Restricted to own data
        elif hasattr(user, 'studentprofile'):
            user_blocks = ScheduleBlock.objects.filter(user_id=user.studentprofile)
            
            block_id = self.request.query_params.get('block_id')
            if block_id:
                if user_blocks.filter(id=block_id).exists():
                    return ScheduleEntry.objects.filter(schedule_block_id=block_id)
                else:
                    return ScheduleEntry.objects.none()
            
            return ScheduleEntry.objects.filter(schedule_block_id__in=user_blocks)
        
        # DEFAULT: No access
        else:
            return ScheduleEntry.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ScheduleEntryCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ScheduleEntryUpdateSerializer
        return ScheduleEntrySerializer
    
    
    def perform_create(self, serializer):
        """
        Never use this in the student views, only for faculty/admin
        """
        
        user = self.request.user
        schedule_block = serializer.validated_data.get('schedule_block_id')
        
        # Students can only create in their own blocks
        if hasattr(user, 'studentprofile'):
            if schedule_block.user_id != user.studentprofile:
                raise serializers.ValidationError("You can only create entries in your own schedule blocks")
        
        # Faculty/Admin can create in any block without restrictions
        serializer.save()