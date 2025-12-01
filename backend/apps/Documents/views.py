from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import *
from .serializers import *


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing document categories"""
    queryset = Category.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['display_order', 'name', 'created_at']
    ordering = ['display_order']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer
    
    def get_permissions(self):
        # Anyone can view categories
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        # Only admins can create/update/delete
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get all documents in this category"""
        category = self.get_object()
        documents = Document.active.filter(category=category)
        
        # Apply user permissions
        if not request.user.is_staff:
            documents = documents.filter(
                Q(uploaded_by=request.user) |
                Q(folder__is_public=True) |
                Q(folder__isnull=True)
            )
        
        serializer = DocumentListSerializer(
            documents, many=True, context={'request': request}
        )
        return Response(serializer.data)


class DocumentTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing document types"""
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]


class FolderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing folders"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'parent', 'is_public']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter folders based on user permissions"""
        queryset = Folder.objects.filter(deleted_at__isnull=True)
        
        # Optimize queries
        queryset = queryset.select_related('category', 'created_by', 'parent')
        queryset = queryset.prefetch_related('subfolders', 'documents')
        
        user = self.request.user
        if not user.is_staff:
            # Non-staff can only see public folders or folders they have access to
            queryset = queryset.filter(
                Q(is_public=True) |
                Q(created_by=user) |
                Q(folder_permissions__user=user) |
                Q(folder_role_permissions__role=user.role_type)
            ).distinct()
        
        return queryset
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return FolderCreateUpdateSerializer
        elif self.action == 'list':
            return FolderListSerializer
        return FolderDetailSerializer
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    def perform_destroy(self, instance):
        """Soft delete folder"""
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user
        instance.save()
    
    @action(detail=True, methods=['get'])
    def breadcrumbs(self, request, pk=None):
        """Get folder breadcrumb trail"""
        folder = self.get_object()
        ancestors = folder.get_ancestors()
        trail = [
            {'id': a.id, 'name': a.name, 'slug': a.slug}
            for a in ancestors
        ]
        trail.append({'id': folder.id, 'name': folder.name, 'slug': folder.slug})
        return Response(trail)
    
    @action(detail=True, methods=['get'])
    def tree(self, request, pk=None):
        """Get folder tree (descendants)"""
        folder = self.get_object()
        descendants = folder.get_descendants()
        serializer = FolderListSerializer(
            descendants, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def set_permissions(self, request, pk=None):
        """Set user-specific permissions for folder"""
        folder = self.get_object()
        
        # Check if user can manage permissions
        if not request.user.is_staff and folder.created_by != request.user:
            return Response(
                {'error': 'You do not have permission to manage folder permissions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = FolderPermissionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(folder=folder)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing documents"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'folder', 'document_type', 'is_featured', 'uploaded_by']
    search_fields = ['title', 'description', 'file_extension']
    ordering_fields = ['title', 'uploaded_at', 'view_count', 'file_size']
    ordering = ['-uploaded_at']
    
    def get_queryset(self):
        """Filter documents based on user permissions"""
        queryset = Document.objects.filter(is_active=True, deleted_at__isnull=True)
        
        # Optimize queries
        queryset = queryset.select_related(
            'category', 'folder', 'document_type', 'uploaded_by', 'approval'
        )
        queryset = queryset.prefetch_related('permissions', 'versions')
        
        user = self.request.user
        
        # Filter based on permissions
        if not user.is_staff:
            queryset = queryset.filter(
                Q(uploaded_by=user) |
                Q(folder__is_public=True) |
                Q(folder__isnull=True) |
                Q(folder__folder_permissions__user=user) |
                Q(folder__folder_role_permissions__role=user.role_type)
            ).distinct()
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DocumentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DocumentUpdateSerializer
        elif self.action == 'list':
            return DocumentListSerializer
        return DocumentDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Increment view count on retrieve"""
        instance = self.get_object()
        
        # Check if user can view
        if not instance.can_user_access(request.user, 'view'):
            return Response(
                {'error': 'You do not have permission to view this document'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Increment view count
        instance.increment_view_count()
        
        # Log view activity
        instance.log_activity(
            action=ActivityLog.ActionTypes.DOCUMENT_VIEW,
            user=request.user,
            description=f"Viewed document '{instance.title}'",
            ip=request.META.get('REMOTE_ADDR')
        )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def perform_destroy(self, instance):
        """Soft delete document"""
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user
        instance.save()
        
        # Log deletion
        instance.log_activity(
            action=ActivityLog.ActionTypes.DOCUMENT_DELETE,
            user=self.request.user,
            description=f"Deleted document '{instance.title}'"
        )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download document file"""
        document = self.get_object()
        
        # Check permissions
        if not document.can_user_access(request.user, 'download'):
            return Response(
                {'error': 'You do not have permission to download this document'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if document can be downloaded
        if not document.can_be_downloaded:
            return Response(
                {'error': 'This document is not available for download'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log download
        document.log_activity(
            action=ActivityLog.ActionTypes.DOCUMENT_DOWNLOAD,
            user=request.user,
            description=f"Downloaded document '{document.title}'",
            ip=request.META.get('REMOTE_ADDR')
        )
        
        # Return file URL
        file_url = request.build_absolute_uri(document.file_path.url)
        return Response({
            'url': file_url,
            'filename': document.file_path.name,
            'size': document.file_size,
            'mime_type': document.mime_type
        })
    
    @action(detail=True, methods=['post'])
    def create_version(self, request, pk=None):
        """Create a new version of the document"""
        document = self.get_object()
        
        # Check permissions
        if not document.can_user_access(request.user, 'edit'):
            return Response(
                {'error': 'You do not have permission to edit this document'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get next version number
        last_version = document.versions.order_by('-version_number').first()
        next_version = (last_version.version_number + 1) if last_version else 1
        
        # Create new version
        version_data = {
            'document': document.id,
            'version_number': next_version,
            'file_path': request.data.get('file_path'),
            'change_notes': request.data.get('change_notes', ''),
            'is_current': True
        }
        
        serializer = DocumentVersionSerializer(data=version_data, context={'request': request})
        if serializer.is_valid():
            # Mark all other versions as not current
            document.versions.update(is_current=False)
            
            # Save new version
            version = serializer.save(uploaded_by=request.user)
            
            # Log version creation
            version.log_activity(
                action=ActivityLog.ActionTypes.VERSION_CREATE,
                user=request.user,
                description=f"Created version {next_version} for '{document.title}'"
            )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Get all versions of the document"""
        document = self.get_object()
        versions = document.versions.all()
        serializer = DocumentVersionSerializer(
            versions, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """Get activity log for document"""
        document = self.get_object()
        activities = document.activities.all()[:50]  # Last 50 activities
        serializer = ActivityLogSerializer(
            activities, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """Bulk soft delete documents"""
        serializer = BulkDeleteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        document_ids = serializer.validated_data['document_ids']
        permanent = serializer.validated_data['permanent']
        
        # Get documents user can delete
        documents = Document.objects.filter(
            id__in=document_ids,
            deleted_at__isnull=True
        )
        
        if not request.user.is_staff:
            documents = documents.filter(uploaded_by=request.user)
        
        count = documents.count()
        
        if permanent:
            # Permanent delete (admin only)
            if not request.user.is_staff:
                return Response(
                    {'error': 'Only admins can permanently delete documents'},
                    status=status.HTTP_403_FORBIDDEN
                )
            documents.delete()
        else:
            # Soft delete
            documents.update(
                deleted_at=timezone.now(),
                deleted_by=request.user
            )
        
        return Response({
            'message': f'Successfully deleted {count} documents',
            'count': count
        })
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured documents"""
        documents = self.get_queryset().filter(is_featured=True)[:10]
        serializer = DocumentListSerializer(
            documents, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recently uploaded documents"""
        documents = self.get_queryset()[:20]
        serializer = DocumentListSerializer(
            documents, many=True, context={'request': request}
        )
        return Response(serializer.data)


class DocumentApprovalViewSet(viewsets.ModelViewSet):
    """ViewSet for managing document approvals"""
    serializer_class = DocumentApprovalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'reviewed_by']
    ordering_fields = ['submitted_at', 'reviewed_at']
    ordering = ['-submitted_at']
    
    def get_queryset(self):
        """Filter approvals based on user role"""
        queryset = DocumentApproval.objects.select_related(
            'document', 'reviewed_by'
        ).prefetch_related('history')
        
        user = self.request.user
        
        if user.is_staff or user.role_type == 'admin':
            # Admins see all approvals
            return queryset
        elif user.role_type == 'faculty':
            # Faculty see approvals for their documents
            return queryset.filter(document__uploaded_by=user)
        else:
            # Students/staff see only their own submitted documents
            return queryset.filter(document__uploaded_by=user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a document"""
        approval = self.get_object()
        
        # Check permissions
        if not request.user.is_staff and request.user.role_type != 'admin':
            return Response(
                {'error': 'Only admins can approve documents'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = DocumentApprovalActionSerializer(
            data={'action': 'approve', 'notes': request.data.get('notes', '')},
            context={'approval': approval}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        approval.status = 'approved'
        approval.reviewed_by = request.user
        approval.review_notes = serializer.validated_data.get('notes', '')
        approval.save()
        
        return Response(DocumentApprovalSerializer(approval).data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a document"""
        approval = self.get_object()
        
        # Check permissions
        if not request.user.is_staff and request.user.role_type != 'admin':
            return Response(
                {'error': 'Only admins can reject documents'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = DocumentApprovalActionSerializer(
            data={'action': 'reject', 'notes': request.data.get('notes', '')},
            context={'approval': approval}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        approval.status = 'rejected'
        approval.reviewed_by = request.user
        approval.review_notes = serializer.validated_data.get('notes', '')
        approval.save()
        
        return Response(DocumentApprovalSerializer(approval).data)
    
    @action(detail=True, methods=['post'])
    def resubmit(self, request, pk=None):
        """Resubmit a rejected document"""
        approval = self.get_object()
        
        # Check if user owns the document
        if approval.document.uploaded_by != request.user:
            return Response(
                {'error': 'You can only resubmit your own documents'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = DocumentApprovalActionSerializer(
            data={'action': 'resubmit', 'notes': request.data.get('notes', '')},
            context={'approval': approval}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        approval.status = 'resubmitted'
        approval.resubmission_notes = serializer.validated_data.get('notes', '')
        approval.save()
        
        return Response(DocumentApprovalSerializer(approval).data)
    
    @action(detail=False, methods=['post'])
    def bulk_approve(self, request):
        """Bulk approve/reject documents"""
        if not request.user.is_staff and request.user.role_type != 'admin':
            return Response(
                {'error': 'Only admins can bulk approve/reject documents'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BulkApproveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        document_ids = serializer.validated_data['document_ids']
        action_type = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')
        
        approvals = DocumentApproval.objects.filter(
            document_id__in=document_ids,
            status='pending'
        )
        
        count = approvals.count()
        new_status = 'approved' if action_type == 'approve' else 'rejected'
        
        approvals.update(
            status=new_status,
            reviewed_by=request.user,
            review_notes=notes,
            reviewed_at=timezone.now()
        )
        
        return Response({
            'message': f'Successfully {action_type}d {count} documents',
            'count': count
        })
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending approvals"""
        approvals = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(approvals, many=True)
        return Response(serializer.data)


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing activity logs (read-only)"""
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['action', 'user', 'content_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter activities based on user permissions"""
        queryset = ActivityLog.objects.select_related(
            'user', 'content_type'
        )
        
        user = self.request.user
        
        if user.is_staff or user.role_type == 'admin':
            return queryset
        
        # Non-admins see only their own activities
        return queryset.filter(user=user)
