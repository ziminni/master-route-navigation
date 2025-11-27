# Example serializers structure for your next step
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Category, DocumentType, Document, DocumentPermission, 
    Tag, DocumentApproval, ApprovalHistory, ActivityLog, DocumentVersion
)

# ============ READ-ONLY SERIALIZERS ============

class CategorySerializer(serializers.ModelSerializer):
    """Basic category serializer"""
    document_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 
                  'display_order', 'document_count', 'created_at', 'updated_at']
        read_only_fields = ['slug', 'created_at', 'updated_at']
    
    def get_document_count(self, obj):
        return obj.documents.filter(is_active=True).count()


class TagSerializer(serializers.ModelSerializer):
    """Basic tag serializer"""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'created_at']
        read_only_fields = ['slug', 'created_at']


class DocumentTypeSerializer(serializers.ModelSerializer):
    """Document type with validation rules"""
    class Meta:
        model = DocumentType
        fields = ['id', 'name', 'slug', 'description', 'allowed_extensions',
                  'max_file_size_mb', 'requires_approval', 'created_at', 'updated_at']
        read_only_fields = ['slug', 'created_at', 'updated_at']


# ============ NESTED SERIALIZERS ============

class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user info for nested serialization"""
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = fields


class ActivityLogSerializer(serializers.ModelSerializer):
    """Activity log with user details"""
    user = UserMinimalSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = ['id', 'user', 'action', 'action_display', 'description', 
                  'metadata', 'created_at']
        read_only_fields = fields


class DocumentPermissionSerializer(serializers.ModelSerializer):
    """Document permissions by role"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = DocumentPermission
        fields = ['id', 'role', 'role_display', 'can_view', 'can_download', 'created_at']
        read_only_fields = ['created_at']


# ============ MAIN DOCUMENT SERIALIZERS ============

class DocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for document lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    file_size_mb = serializers.ReadOnlyField()
    download_count = serializers.ReadOnlyField()
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Document
        fields = ['id', 'title', 'description', 'file_path', 'file_size', 'file_size_mb',
                  'file_extension', 'mime_type', 'category', 'category_name', 
                  'uploaded_by', 'uploaded_by_name', 'document_type', 'tags',
                  'uploaded_at', 'updated_at', 'is_active', 'view_count', 
                  'download_count', 'is_featured']
        read_only_fields = ['uploaded_by', 'file_size', 'file_extension', 'mime_type',
                           'uploaded_at', 'updated_at', 'view_count']


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Detailed document serializer with all relations"""
    category = CategorySerializer(read_only=True)
    document_type = DocumentTypeSerializer(read_only=True)
    uploaded_by = UserMinimalSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    permissions = DocumentPermissionSerializer(many=True, read_only=True)
    recent_activities = serializers.SerializerMethodField()
    
    # Computed fields
    file_size_mb = serializers.ReadOnlyField()
    can_be_downloaded = serializers.ReadOnlyField()
    download_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Document
        fields = ['id', 'title', 'description', 'file_path', 'file_size', 'file_size_mb',
                  'file_extension', 'mime_type', 'category', 'uploaded_by', 
                  'document_type', 'tags', 'permissions', 'uploaded_at', 'updated_at', 
                  'is_active', 'view_count', 'download_count', 'is_featured',
                  'can_be_downloaded', 'recent_activities']
        read_only_fields = ['uploaded_by', 'file_size', 'file_extension', 'mime_type',
                           'uploaded_at', 'updated_at', 'view_count']
    
    def get_recent_activities(self, obj):
        activities = obj.activities.all()[:10]
        return ActivityLogSerializer(activities, many=True).data


class DocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for document creation/upload"""
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Document
        fields = ['title', 'description', 'file_path', 'category', 
                  'document_type', 'tag_ids', 'is_featured']
    
    def validate_file_path(self, value):
        """Validate file size and extension"""
        # Get file size
        file_size = value.size
        
        # Get document type from validated data
        document_type = self.initial_data.get('document_type')
        if document_type:
            doc_type = DocumentType.objects.get(pk=document_type)
            
            # Check file size
            max_size = doc_type.max_file_size_mb * 1024 * 1024
            if file_size > max_size:
                raise serializers.ValidationError(
                    f"File size exceeds maximum allowed ({doc_type.max_file_size_mb}MB)"
                )
            
            # Check file extension
            file_extension = value.name.split('.')[-1].lower()
            if doc_type.allowed_extensions and file_extension not in doc_type.allowed_extensions:
                raise serializers.ValidationError(
                    f"File extension '.{file_extension}' not allowed. "
                    f"Allowed: {', '.join(doc_type.allowed_extensions)}"
                )
        
        return value
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        
        # Set uploaded_by from request context
        validated_data['uploaded_by'] = self.context['request'].user
        
        # Extract file info
        file_obj = validated_data.get('file_path')
        if file_obj:
            validated_data['file_size'] = file_obj.size
            validated_data['file_extension'] = file_obj.name.split('.')[-1].lower()
            # You might want to use python-magic for mime_type
            # validated_data['mime_type'] = magic.from_buffer(file_obj.read(), mime=True)
        
        document = Document.objects.create(**validated_data)
        
        # Add tags
        if tag_ids:
            document.tags.set(tag_ids)
        
        return document


# ============ APPROVAL SERIALIZERS ============

class ApprovalHistorySerializer(serializers.ModelSerializer):
    """Approval history entries"""
    changed_by = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = ApprovalHistory
        fields = ['id', 'status_from', 'status_to', 'changed_by', 
                  'changed_at', 'notes']
        read_only_fields = fields


class DocumentApprovalSerializer(serializers.ModelSerializer):
    """Document approval with history"""
    document_title = serializers.CharField(source='document.title', read_only=True)
    reviewed_by = UserMinimalSerializer(read_only=True)
    history = ApprovalHistorySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DocumentApproval
        fields = ['id', 'document', 'document_title', 'status', 'status_display',
                  'previous_status', 'resubmission_count', 'submitted_at', 
                  'reviewed_at', 'last_resubmitted_at', 'reviewed_by', 
                  'review_notes', 'resubmission_notes', 'history']
        read_only_fields = ['document', 'submitted_at', 'reviewed_at', 
                           'last_resubmitted_at', 'reviewed_by', 'previous_status',
                           'resubmission_count']


class ApprovalActionSerializer(serializers.Serializer):
    """Serializer for approval actions (approve/reject)"""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_action(self, value):
        approval = self.context['approval']
        
        if approval.status == 'approved' and value == 'approve':
            raise serializers.ValidationError("Document is already approved")
        
        if approval.status == 'rejected' and value == 'reject':
            raise serializers.ValidationError("Document is already rejected")
        
        return value


# ============ VERSION SERIALIZERS ============

class DocumentVersionSerializer(serializers.ModelSerializer):
    """Document version history"""
    uploaded_by = UserMinimalSerializer(read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentVersion
        fields = ['id', 'document', 'version_number', 'file_path', 'file_size',
                  'file_size_mb', 'mime_type', 'uploaded_by', 'uploaded_at', 
                  'change_notes', 'is_current']
        read_only_fields = ['document', 'version_number', 'uploaded_by', 
                           'uploaded_at', 'file_size', 'mime_type']
    
    def get_file_size_mb(self, obj):
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0


# ============ USAGE NOTES ============
"""
Usage in views:

# List view
queryset = Document.active.all()
serializer = DocumentListSerializer(queryset, many=True)

# Detail view
document = Document.objects.get(pk=pk)
serializer = DocumentDetailSerializer(document)

# Create view
serializer = DocumentCreateSerializer(
    data=request.data,
    context={'request': request}
)
if serializer.is_valid():
    document = serializer.save()

# Approval action
serializer = ApprovalActionSerializer(
    data=request.data,
    context={'approval': approval, 'request': request}
)
"""
