from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django.contrib.auth import get_user_model
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
    
    def create(self, request, *args, **kwargs):
        """Create a new category - admin only"""
        # Check if user is admin
        if not hasattr(request.user, 'role_type') or request.user.role_type != 'admin':
            if not request.user.is_staff and not request.user.is_superuser:
                return Response(
                    {'error': 'Only admins can create categories'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update a category - admin only"""
        # Check if user is admin
        if not hasattr(request.user, 'role_type') or request.user.role_type != 'admin':
            if not request.user.is_staff and not request.user.is_superuser:
                return Response(
                    {'error': 'Only admins can update categories'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a category - admin only"""
        # Check if user is admin
        if not hasattr(request.user, 'role_type') or request.user.role_type != 'admin':
            if not request.user.is_staff and not request.user.is_superuser:
                return Response(
                    {'error': 'Only admins can delete categories'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().destroy(request, *args, **kwargs)
    
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
    filterset_fields = ['category', 'is_public']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter folders based on user permissions"""
        queryset = Folder.objects.filter(deleted_at__isnull=True)
        
        # Optimize queries
        queryset = queryset.select_related('category', 'created_by', 'parent')
        queryset = queryset.prefetch_related('subfolders', 'documents')
        
        # Handle parent folder filtering explicitly
        parent_param = self.request.query_params.get('parent', None)
        if parent_param is not None:
            if parent_param == '' or parent_param.lower() == 'none':
                # Show only root-level folders (no parent)
                queryset = queryset.filter(parent__isnull=True)
            else:
                # Show folders in specific parent folder
                try:
                    parent_id = int(parent_param)
                    queryset = queryset.filter(parent_id=parent_id)
                except (ValueError, TypeError):
                    queryset = queryset.filter(parent__isnull=True)
        
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
    filterset_fields = ['category', 'document_type', 'is_featured', 'uploaded_by']
    search_fields = ['title', 'description', 'file_extension']
    ordering_fields = ['title', 'uploaded_at', 'view_count', 'file_size']
    ordering = ['-uploaded_at']
    
    def get_queryset(self):
        """Filter documents based on user permissions"""
        # For permanent delete, include deleted documents
        if self.action == 'destroy' and self.request.query_params.get('permanent', 'false').lower() == 'true':
            queryset = Document.objects.filter(is_active=True)  # Include deleted documents
        else:
            queryset = Document.objects.filter(is_active=True, deleted_at__isnull=True)
        
        # Optimize queries
        queryset = queryset.select_related(
            'category', 'folder', 'document_type', 'uploaded_by', 'approval'
        )
        queryset = queryset.prefetch_related('permissions', 'versions')
        
        user = self.request.user
        
        # Handle folder filtering explicitly
        # If folder parameter is provided in query params, filter by that folder
        # If folder parameter is explicitly 'null' or empty, show only root-level documents
        folder_param = self.request.query_params.get('folder', None)
        if folder_param is not None:
            if folder_param == '' or folder_param.lower() == 'null':
                # Show only root-level documents (no folder)
                queryset = queryset.filter(folder__isnull=True)
            else:
                # Show documents in specific folder
                try:
                    folder_id = int(folder_param)
                    queryset = queryset.filter(folder_id=folder_id)
                except (ValueError, TypeError):
                    queryset = queryset.filter(folder__isnull=True)
        
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
        """Soft delete document (or permanent if query param set)"""
        # Check if permanent delete is requested
        permanent = self.request.query_params.get('permanent', 'false').lower() == 'true'
        
        if permanent:
            # Permanent delete - admin only
            if not self.request.user.is_staff and self.request.user.role_type != 'admin':
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Only admins can permanently delete documents")
            
            # Log before deleting
            instance.log_activity(
                action=ActivityLog.ActionTypes.DOCUMENT_DELETE,
                user=self.request.user,
                description=f"PERMANENTLY deleted document '{instance.title}'"
            )
            
            # Actually delete from database
            instance.delete()
        else:
            # Soft delete
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
        
        # Check if file exists
        if not document.file_path:
            return Response(
                {'error': 'Document file not found'},
                status=status.HTTP_404_NOT_FOUND
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
        # Extract just the filename from the path
        import os
        filename = os.path.basename(document.file_path.name)
        return Response({
            'url': file_url,
            'filename': filename,
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
    
    @action(detail=False, methods=['get'], url_path='my-recent')
    def my_recent(self, request):
        """Get current user's recently viewed/accessed documents based on activity log"""
        from django.db.models import Max
        
        # Get document IDs from user's recent activities
        recent_activities = ActivityLog.objects.filter(
            user=request.user,
            action__in=[
                ActivityLog.ActionTypes.DOCUMENT_VIEW,
                ActivityLog.ActionTypes.DOCUMENT_DOWNLOAD,
                ActivityLog.ActionTypes.DOCUMENT_UPLOAD
            ],
            content_type__model='document'
        ).values('object_id').annotate(
            last_accessed=Max('created_at')
        ).order_by('-last_accessed')[:50]
        
        # Get document IDs
        doc_ids = [activity['object_id'] for activity in recent_activities]
        
        # Fetch documents maintaining the order
        documents = self.get_queryset().filter(id__in=doc_ids)
        
        # Preserve activity order
        documents_dict = {doc.id: doc for doc in documents}
        ordered_documents = [documents_dict[doc_id] for doc_id in doc_ids if doc_id in documents_dict]
        
        serializer = DocumentListSerializer(
            ordered_documents, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='my-uploads')
    def my_uploads(self, request):
        """Get documents uploaded by the current user"""
        # Get documents uploaded by the authenticated user
        queryset = self.get_queryset().filter(uploaded_by=request.user)
        
        # Apply sorting
        queryset = queryset.order_by('-uploaded_at')
        
        serializer = DocumentListSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trash(self, request):
        """Get all soft-deleted documents (trash bin)"""
        # Start with base queryset (without deleted_at filter)
        queryset = Document.objects.filter(is_active=True)
        
        # Apply permission filtering
        user = request.user
        if not user.is_staff:
            queryset = queryset.filter(
                Q(uploaded_by=user) |
                Q(folder__is_public=True) |
                Q(folder__isnull=True) |
                Q(folder__folder_permissions__user=user) |
                Q(folder__folder_role_permissions__role=user.role_type)
            ).distinct()
        
        # Filter for deleted documents only
        queryset = queryset.filter(deleted_at__isnull=False)
        
        # Apply optimizations and ordering
        queryset = queryset.select_related(
            'category', 'folder', 'document_type', 'uploaded_by', 'deleted_by'
        ).order_by('-deleted_at')
        
        serializer = DocumentListSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore a soft-deleted document from trash"""
        from .serializers import DocumentRestoreSerializer
        
        # Get document including deleted ones
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if document is actually deleted
        if not document.deleted_at:
            return Response(
                {'error': 'Document is not in trash'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check permissions - only owner or admin can restore
        if not request.user.is_staff and document.uploaded_by != request.user:
            return Response(
                {'error': 'You do not have permission to restore this document'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate and get optional destination folder
        serializer = DocumentRestoreSerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Restore document
        document.deleted_at = None
        document.deleted_by = None
        
        # Update folder if provided
        restore_to_folder_id = serializer.validated_data.get('restore_to_folder_id')
        if restore_to_folder_id is not None:
            try:
                folder = Folder.objects.get(pk=restore_to_folder_id, deleted_at__isnull=True)
                document.folder = folder
            except Folder.DoesNotExist:
                pass  # Keep original folder
        
        document.save()
        
        # Log restore activity
        document.log_activity(
            action=ActivityLog.ActionTypes.DOCUMENT_UPDATE,
            user=request.user,
            description=f"Restored document '{document.title}' from trash"
        )
        
        return Response({
            'message': f"Document '{document.title}' restored successfully",
            'document': DocumentDetailSerializer(document, context={'request': request}).data
        })
    
    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """Move document to a different folder"""
        from .serializers import DocumentMoveSerializer
        
        document = self.get_object()
        
        # Check permissions - owner, admin, or user with edit permission on current folder
        if not request.user.is_staff and document.uploaded_by != request.user:
            if document.folder and not document.folder.can_user_access(request.user, 'edit'):
                return Response(
                    {'error': 'You do not have permission to move this document'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = DocumentMoveSerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        folder_id = serializer.validated_data.get('folder_id')
        old_folder = document.folder
        
        # Move document
        if folder_id is None:
            document.folder = None
            new_location = "root directory"
        else:
            document.folder = Folder.objects.get(pk=folder_id)
            new_location = document.folder.get_full_path()
        
        document.save()
        
        # Log move activity
        old_location = old_folder.get_full_path() if old_folder else "root directory"
        document.log_activity(
            action=ActivityLog.ActionTypes.DOCUMENT_UPDATE,
            user=request.user,
            description=f"Moved document from '{old_location}' to '{new_location}'",
            old_folder_id=old_folder.id if old_folder else None,
            new_folder_id=folder_id
        )
        
        return Response({
            'message': f"Document moved to {new_location}",
            'document': DocumentDetailSerializer(document, context={'request': request}).data
        })
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get document analytics and statistics (Admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can access analytics'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from django.db.models import Count, Sum, Q
        from django.utils import timezone
        from datetime import timedelta
        
        # Calculate date ranges
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        
        # Total documents
        total_documents = Document.objects.filter(is_active=True, deleted_at__isnull=True).count()
        
        # Total storage usage
        total_size = Document.objects.filter(
            is_active=True, deleted_at__isnull=True
        ).aggregate(
            total=Sum('file_size')
        )['total'] or 0
        total_size_mb = total_size / (1024 * 1024)
        
        # Total users
        User = get_user_model()
        total_users = User.objects.filter(is_active=True).count()
        
        # Total downloads
        total_downloads = Document.objects.filter(
            is_active=True, deleted_at__isnull=True
        ).aggregate(
            total=Sum('download_count')
        )['total'] or 0
        
        # Recent uploads (last 7 days)
        recent_uploads = Document.objects.filter(
            is_active=True,
            deleted_at__isnull=True,
            uploaded_at__gte=week_ago
        ).count()
        
        # Active users (last 7 days)
        active_users = ActivityLog.objects.filter(
            created_at__gte=week_ago
        ).values('user').distinct().count()
        
        # Category distribution
        categories = Category.objects.annotate(
            doc_count=Count(
                'documents',
                filter=Q(documents__is_active=True, documents__deleted_at__isnull=True)
            ),
            total_size=Sum(
                'documents__file_size',
                filter=Q(documents__is_active=True, documents__deleted_at__isnull=True)
            )
        ).filter(doc_count__gt=0).order_by('-doc_count')
        
        category_data = [
            {
                'name': cat.name,
                'count': cat.doc_count,
                'size_mb': (cat.total_size or 0) / (1024 * 1024)
            }
            for cat in categories
        ]
        
        # Top documents by views
        top_documents = Document.objects.filter(
            is_active=True,
            deleted_at__isnull=True
        ).order_by('-view_count')[:10]
        
        top_docs_data = [
            {
                'id': doc.id,
                'title': doc.title,
                'views': doc.view_count,
                'downloads': doc.download_count
            }
            for doc in top_documents
        ]
        
        return Response({
            'total_documents': total_documents,
            'total_size_mb': round(total_size_mb, 2),
            'total_users': total_users,
            'total_downloads': total_downloads,
            'recent_uploads': recent_uploads,
            'active_users': active_users,
            'categories': category_data,
            'top_documents': top_docs_data
        })
    
    @action(detail=False, methods=['get'])
    def user_activity(self, request):
        """Get user activity logs (Admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can access user activity'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get filter parameters
        action_filter = request.query_params.get('action', None)
        limit = int(request.query_params.get('limit', 100))
        
        # Query activity logs
        queryset = ActivityLog.objects.select_related(
            'user', 'content_type'
        ).order_by('-created_at')
        
        # Apply action filter
        if action_filter and action_filter != 'all':
            queryset = queryset.filter(action__icontains=action_filter)
        
        # Limit results
        activities = queryset[:limit]
        
        # Format response
        activity_data = []
        for act in activities:
            # Get document title if content_object is a Document
            document_title = '-'
            if act.content_object and isinstance(act.content_object, Document):
                document_title = act.content_object.title
            
            # Get IP address from metadata
            ip_address = act.metadata.get('ip', '-') if act.metadata else '-'
            
            activity_data.append({
                'timestamp': act.created_at.isoformat(),
                'user_name': f"{act.user.first_name} {act.user.last_name}".strip() or act.user.username if act.user else 'System',
                'action': act.get_action_display(),
                'document_title': document_title,
                'ip_address': ip_address,
                'description': act.description
            })
        
        return Response(activity_data)


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
