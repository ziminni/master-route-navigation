from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *

User = get_user_model()


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user info for nested representations"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'role_type']
        read_only_fields = fields
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for document categories"""
    document_count = serializers.SerializerMethodField()
    folder_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 
            'display_order', 'created_at', 'updated_at',
            'document_count', 'folder_count'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
    
    def get_document_count(self, obj):
        return obj.documents.filter(is_active=True, deleted_at__isnull=True).count()
    
    def get_folder_count(self, obj):
        return obj.folders.filter(deleted_at__isnull=True).count()


class CategoryListSerializer(serializers.ModelSerializer):
    """Lightweight category list serializer"""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'display_order']
        read_only_fields = fields


class DocumentTypeSerializer(serializers.ModelSerializer):
    """Serializer for document types"""
    
    class Meta:
        model = DocumentType
        fields = [
            'id', 'name', 'slug', 'description', 'allowed_extensions',
            'max_file_size_mb', 'requires_approval', 'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
    
    def validate_allowed_extensions(self, value):
        """Validate allowed_extensions is a list of strings"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Must be a list of file extensions")
        
        if not all(isinstance(ext, str) for ext in value):
            raise serializers.ValidationError("All extensions must be strings")
        
        # Normalize extensions
        return [ext.lower().lstrip('.') for ext in value if ext]


class FolderPermissionSerializer(serializers.ModelSerializer):
    """Serializer for user-specific folder permissions"""
    user = UserMinimalSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    
    class Meta:
        model = FolderPermission
        fields = [
            'id', 'folder', 'user', 'user_id',
            'can_view', 'can_upload', 'can_edit', 'can_delete',
            'created_at'
        ]
        read_only_fields = ['created_at']


class FolderRolePermissionSerializer(serializers.ModelSerializer):
    """Serializer for role-based folder permissions"""
    
    class Meta:
        model = FolderRolePermission
        fields = [
            'id', 'folder', 'role',
            'can_view', 'can_upload', 'can_edit', 'can_delete',
            'created_at'
        ]
        read_only_fields = ['created_at']


class FolderListSerializer(serializers.ModelSerializer):
    """Lightweight folder list serializer"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    subfolder_count = serializers.SerializerMethodField()
    document_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Folder
        fields = [
            'id', 'name', 'slug', 'parent', 'category', 'category_name',
            'is_public', 'subfolder_count', 'document_count', 'created_at'
        ]
        read_only_fields = ['slug', 'created_at']
    
    def get_subfolder_count(self, obj):
        return obj.subfolders.filter(deleted_at__isnull=True).count()
    
    def get_document_count(self, obj):
        return obj.documents.filter(is_active=True, deleted_at__isnull=True).count()


class FolderDetailSerializer(serializers.ModelSerializer):
    """Detailed folder serializer with nested data"""
    category = CategoryListSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    parent_folder = serializers.SerializerMethodField()
    created_by = UserMinimalSerializer(read_only=True)
    deleted_by = UserMinimalSerializer(read_only=True)
    
    # Nested relationships
    subfolders = FolderListSerializer(many=True, read_only=True)
    folder_permissions = FolderPermissionSerializer(many=True, read_only=True)
    folder_role_permissions = FolderRolePermissionSerializer(many=True, read_only=True)
    
    # Computed fields
    full_path = serializers.CharField(source='get_full_path', read_only=True)
    ancestors = serializers.SerializerMethodField()
    
    class Meta:
        model = Folder
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'parent_folder',
            'category', 'category_id', 'created_by', 'is_public',
            'created_at', 'updated_at', 'deleted_at', 'deleted_by',
            'full_path', 'ancestors', 'subfolders',
            'folder_permissions', 'folder_role_permissions'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
    
    def get_parent_folder(self, obj):
        if obj.parent:
            return {
                'id': obj.parent.id,
                'name': obj.parent.name,
                'slug': obj.parent.slug
            }
        return None
    
    def get_ancestors(self, obj):
        """Get breadcrumb trail"""
        ancestors = obj.get_ancestors()
        return [{'id': a.id, 'name': a.name, 'slug': a.slug} for a in ancestors]


class FolderCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating folders"""
    
    class Meta:
        model = Folder
        fields = [
            'id', 'name', 'slug', 'description', 'parent',
            'category', 'is_public'
        ]
        read_only_fields = ['slug']
    
    def validate(self, attrs):
        """Validate folder creation/update"""
        # Check for circular references
        parent = attrs.get('parent')
        if parent and self.instance:
            current = parent
            while current:
                if current.id == self.instance.id:
                    raise serializers.ValidationError({
                        'parent': 'Cannot set folder as its own ancestor (circular reference)'
                    })
                current = current.parent
        
        return attrs


class DocumentPermissionSerializer(serializers.ModelSerializer):
    """Serializer for document role-based permissions"""
    
    class Meta:
        model = DocumentPermission
        fields = [
            'id', 'document', 'role',
            'can_view', 'can_download', 'can_edit', 'can_delete',
            'created_at'
        ]
        read_only_fields = ['created_at']


class DocumentVersionSerializer(serializers.ModelSerializer):
    """Serializer for document versions"""
    uploaded_by = UserMinimalSerializer(read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentVersion
        fields = [
            'id', 'document', 'version_number', 'file_path', 'file_url',
            'file_size', 'file_size_mb', 'mime_type', 'uploaded_by',
            'uploaded_at', 'change_notes', 'is_current'
        ]
        read_only_fields = ['uploaded_at']
    
    def get_file_size_mb(self, obj):
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0
    
    def get_file_url(self, obj):
        if obj.file_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file_path.url)
        return None


class ApprovalHistorySerializer(serializers.ModelSerializer):
    """Serializer for approval history"""
    changed_by = UserMinimalSerializer(read_only=True)
    status_from_display = serializers.SerializerMethodField()
    status_to_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ApprovalHistory
        fields = [
            'id', 'approval', 'status_from', 'status_from_display',
            'status_to', 'status_to_display', 'changed_by',
            'changed_at', 'notes'
        ]
        read_only_fields = fields
    
    def get_status_from_display(self, obj):
        return obj.status_from.title() if obj.status_from else None
    
    def get_status_to_display(self, obj):
        return obj.status_to.title()


class DocumentApprovalSerializer(serializers.ModelSerializer):
    """Serializer for document approvals"""
    document_title = serializers.CharField(source='document.title', read_only=True)
    reviewed_by = UserMinimalSerializer(read_only=True)
    history = ApprovalHistorySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DocumentApproval
        fields = [
            'id', 'document', 'document_title', 'status', 'status_display',
            'previous_status', 'resubmission_count', 'submitted_at',
            'reviewed_at', 'last_resubmitted_at', 'reviewed_by',
            'review_notes', 'resubmission_notes', 'history'
        ]
        read_only_fields = [
            'submitted_at', 'reviewed_at', 'last_resubmitted_at',
            'previous_status', 'resubmission_count'
        ]
    
    def validate(self, attrs):
        """Validate status transitions"""
        if self.instance:
            # Validation is handled in model's clean() method
            instance = self.instance
            instance.status = attrs.get('status', instance.status)
            try:
                instance.clean()
            except Exception as e:
                raise serializers.ValidationError({'status': str(e)})
        return attrs


class DocumentApprovalActionSerializer(serializers.Serializer):
    """Serializer for approval actions (approve/reject/resubmit)"""
    action = serializers.ChoiceField(choices=['approve', 'reject', 'resubmit'])
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_action(self, value):
        """Validate action is allowed for current status"""
        approval = self.context.get('approval')
        if not approval:
            return value
        
        status = approval.status
        allowed_actions = {
            'pending': ['approve', 'reject'],
            'rejected': ['resubmit'],
            'resubmitted': ['approve', 'reject'],
            'approved': []
        }
        
        if value not in allowed_actions.get(status, []):
            raise serializers.ValidationError(
                f"Cannot {value} document with status '{status}'"
            )
        
        return value


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for activity logs"""
    user = UserMinimalSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    content_type_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'content_type', 'content_type_name', 'object_id',
            'user', 'action', 'action_display', 'description',
            'metadata', 'created_at'
        ]
        read_only_fields = fields
    
    def get_content_type_name(self, obj):
        return obj.content_type.model if obj.content_type else None


class DocumentListSerializer(serializers.ModelSerializer):
    """Lightweight document list serializer"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    folder_name = serializers.CharField(source='folder.name', read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    can_download = serializers.BooleanField(source='can_be_downloaded', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'file_extension', 'mime_type',
            'file_size', 'file_size_mb', 'file_url', 'category', 'category_name',
            'folder', 'folder_name', 'uploaded_by_name', 'uploaded_at',
            'view_count', 'is_featured', 'is_active', 'can_download', 'deleted_at'
        ]
        read_only_fields = fields
    
    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip() or obj.uploaded_by.username
        return None
    
    def get_file_size_mb(self, obj):
        return obj.file_size_mb
    
    def get_file_url(self, obj):
        if obj.file_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file_path.url)
        return None


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Detailed document serializer with all related data"""
    category = CategoryListSerializer(read_only=True)
    folder = FolderListSerializer(read_only=True)
    document_type = DocumentTypeSerializer(read_only=True)
    uploaded_by = UserMinimalSerializer(read_only=True)
    deleted_by = UserMinimalSerializer(read_only=True)
    
    # Nested relationships
    permissions = DocumentPermissionSerializer(many=True, read_only=True)
    versions = DocumentVersionSerializer(many=True, read_only=True)
    approval = DocumentApprovalSerializer(read_only=True)
    
    # Computed fields
    file_size_mb = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    can_download = serializers.BooleanField(source='can_be_downloaded', read_only=True)
    download_count = serializers.SerializerMethodField()
    recent_activities = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'file_path', 'file_url',
            'file_size', 'file_size_mb', 'file_extension', 'mime_type',
            'category', 'folder', 'document_type', 'uploaded_by',
            'uploaded_at', 'updated_at', 'is_active', 'view_count',
            'is_featured', 'can_download', 'download_count',
            'deleted_at', 'deleted_by', 'permissions', 'versions',
            'approval', 'recent_activities'
        ]
        read_only_fields = [
            'file_size', 'file_extension', 'mime_type', 'uploaded_at',
            'updated_at', 'view_count'
        ]
    
    def get_file_size_mb(self, obj):
        return obj.file_size_mb
    
    def get_file_url(self, obj):
        if obj.file_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file_path.url)
        return None
    
    def get_download_count(self, obj):
        # Note: This makes a DB query. Consider using annotations in viewset
        return obj.get_download_count()
    
    def get_recent_activities(self, obj):
        """Get last 5 activities for this document"""
        activities = obj.activities.all()[:5]
        return ActivityLogSerializer(activities, many=True, context=self.context).data


class DocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating documents"""
    
    class Meta:
        model = Document
        fields = [
            'title', 'description', 'file_path', 'category',
            'folder', 'document_type', 'is_featured'
        ]
    
    def validate_file_path(self, value):
        """Validate file upload"""
        if not value:
            raise serializers.ValidationError("File is required")
        
        # Check file size
        if value.size > 100 * 1024 * 1024:  # 100MB max
            raise serializers.ValidationError("File size cannot exceed 100MB")
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        document_type = attrs.get('document_type')
        file_path = attrs.get('file_path')
        
        if document_type and file_path:
            # Validate file extension
            import os
            _, ext = os.path.splitext(file_path.name)
            ext = ext.lower().lstrip('.')
            
            allowed = document_type.allowed_extensions
            if allowed and ext not in allowed:
                raise serializers.ValidationError({
                    'file_path': f"File extension '{ext}' not allowed. Allowed: {', '.join(allowed)}"
                })
            
            # Validate file size
            max_size = document_type.max_file_size_mb * 1024 * 1024
            if file_path.size > max_size:
                raise serializers.ValidationError({
                    'file_path': f"File size exceeds maximum allowed ({document_type.max_file_size_mb}MB)"
                })
        
        return attrs
    
    def create(self, validated_data):
        """Create document and set uploaded_by from request user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['uploaded_by'] = request.user
        
        document = Document.objects.create(**validated_data)
        
        # Create approval if document type requires it
        if document.document_type and document.document_type.requires_approval:
            DocumentApproval.objects.create(document=document)
        
        return document


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating documents"""
    
    class Meta:
        model = Document
        fields = [
            'title', 'description', 'category', 'folder',
            'document_type', 'is_featured', 'is_active'
        ]
    
    def validate(self, attrs):
        """Validate updates don't break existing approvals"""
        if self.instance:
            # If document is approved and we're changing critical fields
            if hasattr(self.instance, 'approval'):
                if self.instance.approval.status == 'approved':
                    if 'document_type' in attrs and attrs['document_type'] != self.instance.document_type:
                        raise serializers.ValidationError({
                            'document_type': 'Cannot change document type of approved document'
                        })
        
        return attrs


class BulkDeleteSerializer(serializers.Serializer):
    """Serializer for bulk delete operations"""
    document_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    permanent = serializers.BooleanField(default=False)
    
    def validate_document_ids(self, value):
        if len(value) > 100:
            raise serializers.ValidationError("Cannot delete more than 100 documents at once")
        return value


class BulkApproveSerializer(serializers.Serializer):
    """Serializer for bulk approval operations"""
    document_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_document_ids(self, value):
        if len(value) > 50:
            raise serializers.ValidationError("Cannot process more than 50 documents at once")
        return value


class DocumentMoveSerializer(serializers.Serializer):
    """Serializer for moving document to a folder"""
    folder_id = serializers.IntegerField(allow_null=True, required=False)
    
    def validate_folder_id(self, value):
        """Validate folder exists and user has permission"""
        if value is None:
            return None
        
        from .models import Folder
        try:
            folder = Folder.objects.get(pk=value, deleted_at__isnull=True)
        except Folder.DoesNotExist:
            raise serializers.ValidationError("Folder not found or has been deleted")
        
        # Check if user can upload to this folder
        user = self.context.get('request').user
        if not folder.can_user_access(user, 'upload'):
            raise serializers.ValidationError("You do not have permission to move documents to this folder")
        
        return value


class DocumentRestoreSerializer(serializers.Serializer):
    """Serializer for restoring deleted documents"""
    restore_to_folder_id = serializers.IntegerField(allow_null=True, required=False)
    
    def validate_restore_to_folder_id(self, value):
        """Validate destination folder if provided"""
        if value is None:
            return None
        
        from .models import Folder
        try:
            folder = Folder.objects.get(pk=value, deleted_at__isnull=True)
        except Folder.DoesNotExist:
            raise serializers.ValidationError("Destination folder not found")
        
        return value

