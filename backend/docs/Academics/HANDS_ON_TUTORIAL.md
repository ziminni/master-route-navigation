# 🎓 Hands-On Tutorial: Implementing Hierarchical Serializers

## Your Learning Path

This tutorial walks you through implementing the 4-level serializer hierarchy for your Documents app, **step by step, with exercises**.

---

## Prerequisites Check

Before starting, verify you have:

```python
# ✅ Models defined (you already have these)
from .models import (
    Category, DocumentType, Document, 
    Tag, DocumentPermission, DocumentApproval
)

# ✅ Django REST Framework installed
# pip install djangorestframework

# ✅ Settings configured
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}
```

---

## Part 1: Start Simple - Minimal Serializers (Level 1)

### Step 1.1: Create CategoryMinimalSerializer

**Goal:** Create the simplest serializer - just enough for a dropdown

```python
# In serializers.py
from rest_framework import serializers
from .models import Category

class CategoryMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal category representation for:
    - Dropdown selects
    - Foreign key displays
    - Nested in other serializers
    """
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon']
        read_only_fields = fields  # All fields are read-only
```

**Why these fields?**
- `id` - Required for form submissions
- `name` - Human-readable display
- `slug` - For URLs (if needed)
- `icon` - For UI display with icon

**Test it:**

```python
# In Django shell
from apps.Documents.models import Category
from apps.Documents.serializers import CategoryMinimalSerializer

# Create test data
category = Category.objects.create(
    name="Academic Records",
    description="Official academic documents",
    icon="📚"
)

# Serialize
serializer = CategoryMinimalSerializer(category)
print(serializer.data)
# Output: {'id': 1, 'name': 'Academic Records', 'slug': 'academic-records', 'icon': '📚'}
```

---

### 🎯 Exercise 1: Create TagMinimalSerializer

**Your turn!** Create a minimal serializer for Tag model.

**Requirements:**
- Include: `id`, `name`, `slug`
- All fields read-only
- Add docstring explaining usage

<details>
<summary>💡 Solution (click to reveal)</summary>

```python
class TagMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal tag representation for:
    - Tag badges/chips
    - Document tag lists
    - Tag selection interface
    """
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']
        read_only_fields = fields
```

</details>

---

### 🎯 Exercise 2: Create DocumentTypeMinimalSerializer

**Challenge:** Create minimal serializer for DocumentType

**Hint:** Think about what info you need when displaying document type in a list

<details>
<summary>💡 Solution</summary>

```python
class DocumentTypeMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal document type for display purposes
    """
    
    class Meta:
        model = DocumentType
        fields = ['id', 'name', 'slug']
        read_only_fields = fields
```

</details>

---

## Part 2: Build List Serializers (Level 2)

### Step 2.1: Create CategoryListSerializer

**Goal:** Show categories with basic stats for browsing

```python
from django.db.models import Count

class CategoryListSerializer(serializers.ModelSerializer):
    """
    Category representation for list views with document count
    """
    document_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 
            'icon', 'display_order', 'document_count'
        ]
        read_only_fields = ['slug']
    
    def get_document_count(self, obj):
        """Count only active documents"""
        return obj.documents.filter(is_active=True).count()
```

**⚠️ Performance Warning:** The `get_document_count` above causes N+1 queries!

**Better approach:**

```python
# In your ViewSet
from django.db.models import Count

class CategoryViewSet(viewsets.ModelViewSet):
    
    def get_queryset(self):
        # Annotate count in database query
        return Category.objects.annotate(
            document_count=Count('documents', filter=Q(documents__is_active=True))
        )

# In serializer
class CategoryListSerializer(serializers.ModelSerializer):
    document_count = serializers.IntegerField(read_only=True)
    # No SerializerMethodField needed! Comes from annotation
```

---

### Step 2.2: Create DocumentListSerializer

**Goal:** Show documents in a table/grid efficiently

```python
from django.contrib.auth import get_user_model

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user info for nested display"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email']
        read_only_fields = fields
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class DocumentListSerializer(serializers.ModelSerializer):
    """
    Lightweight document serializer for list views:
    - Document library grid
    - Search results
    - Category document list
    """
    
    # Simple direct access (no extra query if select_related used)
    category_name = serializers.CharField(
        source='category.name',
        read_only=True
    )
    
    # Computed property from model
    file_size_mb = serializers.ReadOnlyField()
    download_count = serializers.ReadOnlyField()
    
    # Nested minimal serializers
    tags = TagMinimalSerializer(many=True, read_only=True)
    
    # Custom display field
    uploader_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'description',
            'file_extension',
            'file_size_mb',
            'category_name',
            'uploader_name',
            'tags',
            'uploaded_at',
            'view_count',
            'download_count',
            'is_featured',
            'is_active'
        ]
    
    def get_uploader_name(self, obj):
        """Format: 'John D.' or 'Unknown'"""
        if obj.uploaded_by:
            first = obj.uploaded_by.first_name
            last = obj.uploaded_by.last_name
            if first and last:
                return f"{first} {last[0]}."
            return obj.uploaded_by.username
        return "Unknown"
```

**ViewSet with optimization:**

```python
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.active.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentListSerializer
        # ... other actions
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        if self.action == 'list':
            # Optimize for list view
            qs = qs.select_related(
                'category',       # ForeignKey - use select_related
                'uploaded_by'     # ForeignKey
            ).prefetch_related(
                'tags'            # ManyToMany - use prefetch_related
            )
        
        return qs
```

---

### 🎯 Exercise 3: Test Query Performance

**Task:** Compare query counts with and without optimization

```python
# In Django shell or create a management command

from django.test.utils import override_settings
from django.db import connection, reset_queries
from apps.Documents.models import Document
from apps.Documents.serializers import DocumentListSerializer

# Create test data first
from apps.Documents.models import Category, Tag
cat = Category.objects.create(name="Test Category")
for i in range(20):
    doc = Document.objects.create(
        title=f"Document {i}",
        category=cat,
        uploaded_by=user  # Use your test user
    )
    doc.tags.set(Tag.objects.all()[:3])

# Test WITHOUT optimization
reset_queries()
documents = Document.objects.all()[:20]
serializer = DocumentListSerializer(documents, many=True)
data = serializer.data
print(f"Queries without optimization: {len(connection.queries)}")
# Expected: 60+ queries (1 + 20 for categories + 20 for tags + ...)

# Test WITH optimization
reset_queries()
documents = Document.objects.select_related(
    'category', 'uploaded_by'
).prefetch_related('tags')[:20]
serializer = DocumentListSerializer(documents, many=True)
data = serializer.data
print(f"Queries with optimization: {len(connection.queries)}")
# Expected: 3-4 queries only!
```

**Questions to answer:**
1. How many queries without optimization?
2. How many queries with optimization?
3. Which queries are causing the N+1 problem?

---

## Part 3: Create Detail Serializers (Level 3)

### Step 3.1: Create DocumentDetailSerializer

**Goal:** Full document information for detail view

```python
class DocumentDetailSerializer(serializers.ModelSerializer):
    """
    Complete document information for:
    - Document detail page
    - Document edit form (pre-populated)
    - Full document API endpoint
    """
    
    # Nested LIST serializers (not Detail!)
    category = CategoryListSerializer(read_only=True)
    document_type = DocumentTypeListSerializer(read_only=True)
    uploaded_by = UserMinimalSerializer(read_only=True)
    
    # ManyToMany with minimal info
    tags = TagMinimalSerializer(many=True, read_only=True)
    
    # Reverse relations
    permissions = serializers.SerializerMethodField()
    
    # Computed properties from model
    file_size_mb = serializers.ReadOnlyField()
    can_be_downloaded = serializers.ReadOnlyField()
    download_count = serializers.ReadOnlyField()
    
    # Complex computed fields
    recent_activities = serializers.SerializerMethodField()
    approval_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            # Basic info
            'id', 'title', 'description',
            
            # File info
            'file_path', 'file_size', 'file_size_mb',
            'file_extension', 'mime_type',
            
            # Relations (expanded)
            'category', 'document_type', 'uploaded_by', 'tags',
            
            # Permissions
            'permissions',
            
            # Timestamps
            'uploaded_at', 'updated_at',
            
            # Status flags
            'is_active', 'is_featured',
            
            # Computed fields
            'view_count', 'download_count', 'can_be_downloaded',
            
            # Complex computed
            'recent_activities', 'approval_status'
        ]
    
    def get_permissions(self, obj):
        """Document permissions by role"""
        from .models import DocumentPermission
        perms = obj.permissions.all()
        return [{
            'role': p.role,
            'role_display': p.get_role_display(),
            'can_view': p.can_view,
            'can_download': p.can_download
        } for p in perms]
    
    def get_recent_activities(self, obj):
        """Last 10 activities"""
        # Only if activities are prefetched
        if hasattr(obj, '_prefetched_objects_cache') and 'activities' in obj._prefetched_objects_cache:
            activities = list(obj.activities.all()[:10])
        else:
            activities = obj.activities.select_related('user').order_by('-created_at')[:10]
        
        return [{
            'id': act.id,
            'action': act.get_action_display(),
            'user': act.user.username if act.user else 'System',
            'created_at': act.created_at,
            'description': act.description
        } for act in activities]
    
    def get_approval_status(self, obj):
        """Approval information if exists"""
        if hasattr(obj, 'approval'):
            return {
                'status': obj.approval.status,
                'status_display': obj.approval.get_status_display(),
                'submitted_at': obj.approval.submitted_at,
                'reviewed_by': obj.approval.reviewed_by.username if obj.approval.reviewed_by else None,
                'reviewed_at': obj.approval.reviewed_at,
                'review_notes': obj.approval.review_notes
            }
        return None
```

**ViewSet retrieve method:**

```python
class DocumentViewSet(viewsets.ModelViewSet):
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentListSerializer
        elif self.action == 'retrieve':
            return DocumentDetailSerializer
        # ... other actions
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        if self.action == 'retrieve':
            # Heavy optimization for detail view
            from django.db.models import Prefetch
            from .models import ActivityLog
            
            qs = qs.select_related(
                'category',
                'document_type',
                'uploaded_by',
                'approval',
                'approval__reviewed_by'
            ).prefetch_related(
                'tags',
                'permissions',
                Prefetch(
                    'activities',
                    queryset=ActivityLog.objects.select_related('user').order_by('-created_at')[:10]
                )
            )
        
        return qs
```

---

### 🎯 Exercise 4: Add Version Information

**Challenge:** Add version information to `DocumentDetailSerializer`

**Requirements:**
- Add `version_info` field (SerializerMethodField)
- Return: current version number, total versions, latest change notes
- Optimize queries

<details>
<summary>💡 Solution</summary>

```python
class DocumentDetailSerializer(serializers.ModelSerializer):
    # ... existing fields ...
    version_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            # ... existing fields ...
            'version_info'
        ]
    
    def get_version_info(self, obj):
        """Version information"""
        # Check if versions are prefetched
        if hasattr(obj, '_prefetched_objects_cache') and 'versions' in obj._prefetched_objects_cache:
            versions = list(obj.versions.all())
        else:
            versions = list(obj.versions.all())
        
        current = next((v for v in versions if v.is_current), None)
        
        return {
            'current_version': current.version_number if current else 1,
            'total_versions': len(versions),
            'has_versions': len(versions) > 1,
            'latest_change_notes': current.change_notes if current else None
        }

# Update get_queryset for retrieve action:
def get_queryset(self):
    # ... existing code ...
    if self.action == 'retrieve':
        qs = qs.prefetch_related(
            # ... existing prefetches ...
            'versions'  # Add this
        )
    return qs
```

</details>

---

## Part 4: Implement Write Serializers (Level 4)

### Step 4.1: Create DocumentCreateSerializer

**Goal:** Handle document upload with validation

```python
class DocumentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new documents with file upload.
    
    Key features:
    - File validation (size, extension)
    - Automatic metadata extraction
    - Tag assignment
    - Activity logging
    """
    
    # Write-only fields (IDs instead of objects)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        help_text="Category ID for the document"
    )
    
    document_type_id = serializers.PrimaryKeyRelatedField(
        queryset=DocumentType.objects.all(),
        source='document_type',
        write_only=True,
        required=False,
        help_text="Document type ID (optional)"
    )
    
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of tag IDs"
    )
    
    # File field
    file_path = serializers.FileField(
        help_text="Document file to upload"
    )
    
    class Meta:
        model = Document
        fields = [
            'title',
            'description',
            'file_path',
            'category_id',
            'document_type_id',
            'tag_ids',
            'is_featured'
        ]
    
    def validate_file_path(self, value):
        """
        Validate uploaded file:
        - Check size
        - Check extension
        - Scan for malware (if integrated)
        """
        # Check file size (max 100MB by default)
        max_size = 100 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size ({value.size / (1024*1024):.1f}MB) exceeds "
                f"maximum allowed (100MB)"
            )
        
        # Check extension
        ext = value.name.split('.')[-1].lower()
        allowed_extensions = [
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 
            'ppt', 'pptx', 'txt', 'csv'
        ]
        
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type '.{ext}' not allowed. "
                f"Allowed types: {', '.join(allowed_extensions)}"
            )
        
        return value
    
    def validate(self, attrs):
        """
        Cross-field validation:
        - Check file against document type rules
        - Verify user has upload permission
        """
        document_type = attrs.get('document_type')
        file_path = attrs.get('file_path')
        
        if document_type and file_path:
            # Check extension against document type
            ext = file_path.name.split('.')[-1].lower()
            
            if document_type.allowed_extensions:
                if ext not in document_type.allowed_extensions:
                    raise serializers.ValidationError({
                        'file_path': (
                            f"File extension '.{ext}' not allowed for "
                            f"{document_type.name}. Allowed: "
                            f"{', '.join(document_type.allowed_extensions)}"
                        )
                    })
            
            # Check size against document type max
            max_size = document_type.max_file_size_mb * 1024 * 1024
            if file_path.size > max_size:
                raise serializers.ValidationError({
                    'file_path': (
                        f"File size exceeds maximum allowed for "
                        f"{document_type.name} ({document_type.max_file_size_mb}MB)"
                    )
                })
        
        return attrs
    
    def create(self, validated_data):
        """
        Create document with:
        - Automatic metadata extraction
        - Tag assignment
        - Approval creation (if required)
        - Activity logging
        """
        from .models import DocumentApproval, ActivityLog
        
        # Extract many-to-many (can't set on unsaved instance)
        tag_ids = validated_data.pop('tag_ids', [])
        
        # Set uploaded_by from request user
        request = self.context.get('request')
        validated_data['uploaded_by'] = request.user
        
        # Extract file metadata
        file_obj = validated_data.get('file_path')
        if file_obj:
            validated_data['file_size'] = file_obj.size
            validated_data['file_extension'] = file_obj.name.split('.')[-1].lower()
            
            # You can use python-magic for accurate MIME type
            # import magic
            # validated_data['mime_type'] = magic.from_buffer(
            #     file_obj.read(1024), 
            #     mime=True
            # )
            # file_obj.seek(0)  # Reset file pointer
        
        # Create document
        document = Document.objects.create(**validated_data)
        
        # Set tags
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids)
            document.tags.set(tags)
        
        # Create approval if document type requires it
        if document.document_type and document.document_type.requires_approval:
            DocumentApproval.objects.create(
                document=document,
                status='pending'
            )
        
        # Log activity
        document.log_activity(
            action=ActivityLog.ActionTypes.DOCUMENT_UPLOAD,
            user=request.user,
            description=f"Document '{document.title}' uploaded",
            file_size=document.file_size,
            file_extension=document.file_extension
        )
        
        return document
```

---

### Step 4.2: Create DocumentUpdateSerializer

**Goal:** Update metadata without changing file

```python
class DocumentUpdateSerializer(serializers.ModelSerializer):
    """
    Update document metadata (not file).
    
    For file replacement, use separate endpoint/serializer.
    """
    
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    
    document_type_id = serializers.PrimaryKeyRelatedField(
        queryset=DocumentType.objects.all(),
        source='document_type',
        write_only=True,
        required=False
    )
    
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Document
        fields = [
            'title',
            'description',
            'category_id',
            'document_type_id',
            'tag_ids',
            'is_featured',
            'is_active'
        ]
    
    def update(self, instance, validated_data):
        """
        Update document metadata:
        - Regular fields
        - Tags
        - Activity logging
        """
        from .models import ActivityLog
        
        # Extract many-to-many
        tag_ids = validated_data.pop('tag_ids', None)
        
        # Track changes for logging
        changes = []
        
        # Update regular fields
        for attr, value in validated_data.items():
            old_value = getattr(instance, attr)
            if old_value != value:
                changes.append(f"{attr}: {old_value} → {value}")
                setattr(instance, attr, value)
        
        instance.save()
        
        # Update tags if provided
        if tag_ids is not None:
            old_tags = set(instance.tags.values_list('id', flat=True))
            new_tags = set(tag_ids)
            if old_tags != new_tags:
                instance.tags.set(tag_ids)
                changes.append("tags updated")
        
        # Log activity
        request = self.context.get('request')
        if changes:
            instance.log_activity(
                action=ActivityLog.ActionTypes.DOCUMENT_UPDATE,
                user=request.user,
                description=f"Document updated: {', '.join(changes)}",
                changes=changes
            )
        
        return instance
```

---

### 🎯 Exercise 5: Create DocumentFileUpdateSerializer

**Challenge:** Create serializer for replacing document file (creates version)

**Requirements:**
- Accept new file
- Accept change notes
- Validate new file
- Create `DocumentVersion` with old file
- Update document with new file
- Log activity

<details>
<summary>💡 Solution</summary>

```python
class DocumentFileUpdateSerializer(serializers.ModelSerializer):
    """Replace document file and create version"""
    
    file_path = serializers.FileField(
        help_text="New file to replace current document"
    )
    
    change_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Describe what changed in this version"
    )
    
    class Meta:
        model = Document
        fields = ['file_path', 'change_notes']
    
    def validate_file_path(self, value):
        """Validate new file"""
        # Same validation as create
        max_size = 100 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File too large")
        
        ext = value.name.split('.')[-1].lower()
        allowed = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']
        if ext not in allowed:
            raise serializers.ValidationError(f"File type not allowed")
        
        return value
    
    def update(self, instance, validated_data):
        """Create version and update file"""
        from .models import DocumentVersion, ActivityLog
        
        change_notes = validated_data.pop('change_notes', '')
        request = self.context.get('request')
        
        # Get next version number
        latest = instance.versions.order_by('-version_number').first()
        new_version_number = (latest.version_number + 1) if latest else 2
        
        # Mark all versions as not current
        instance.versions.update(is_current=False)
        
        # Create version from OLD file
        DocumentVersion.objects.create(
            document=instance,
            version_number=new_version_number - 1,
            file_path=instance.file_path,
            file_size=instance.file_size,
            mime_type=instance.mime_type,
            uploaded_by=instance.uploaded_by,
            change_notes="Previous version",
            is_current=False
        )
        
        # Update document with NEW file
        new_file = validated_data['file_path']
        instance.file_path = new_file
        instance.file_size = new_file.size
        instance.file_extension = new_file.name.split('.')[-1].lower()
        instance.save()
        
        # Create version for NEW file
        DocumentVersion.objects.create(
            document=instance,
            version_number=new_version_number,
            file_path=instance.file_path,
            file_size=instance.file_size,
            mime_type=instance.mime_type,
            uploaded_by=request.user,
            change_notes=change_notes,
            is_current=True
        )
        
        # Log activity
        instance.log_activity(
            action=ActivityLog.ActionTypes.VERSION_CREATE,
            user=request.user,
            description=f"File updated to version {new_version_number}",
            version=new_version_number,
            change_notes=change_notes
        )
        
        return instance
```

**Add to ViewSet:**

```python
class DocumentViewSet(viewsets.ModelViewSet):
    
    @action(detail=True, methods=['patch'], url_path='update-file')
    def update_file(self, request, pk=None):
        """Custom action for file replacement"""
        document = self.get_object()
        
        serializer = DocumentFileUpdateSerializer(
            document,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return full document with detail serializer
        return Response(
            DocumentDetailSerializer(document).data,
            status=status.HTTP_200_OK
        )
```

</details>

---

## Part 5: Complete ViewSet Implementation

### Step 5.1: Full DocumentViewSet

**Goal:** Tie everything together with proper action routing

```python
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Prefetch

class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Document CRUD operations.
    
    Endpoints:
    - GET    /api/documents/              - List documents
    - POST   /api/documents/              - Create document
    - GET    /api/documents/{id}/         - Get document detail
    - PUT    /api/documents/{id}/         - Update document
    - PATCH  /api/documents/{id}/         - Partial update
    - DELETE /api/documents/{id}/         - Delete document
    - PATCH  /api/documents/{id}/update-file/  - Replace file
    - POST   /api/documents/{id}/download/     - Download (log activity)
    """
    
    queryset = Document.active.all()
    
    # Filtering
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ['category', 'document_type', 'is_featured', 'uploaded_by']
    search_fields = ['title', 'description']
    ordering_fields = ['uploaded_at', 'title', 'view_count', 'file_size']
    ordering = ['-uploaded_at']  # Default ordering
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return DocumentListSerializer
        elif self.action == 'retrieve':
            return DocumentDetailSerializer
        elif self.action == 'create':
            return DocumentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DocumentUpdateSerializer
        return DocumentDetailSerializer
    
    def get_queryset(self):
        """Optimize queries based on action"""
        qs = super().get_queryset()
        
        if self.action == 'list':
            # Light optimization for list
            qs = qs.select_related(
                'category',
                'uploaded_by'
            ).prefetch_related(
                'tags'
            )
        
        elif self.action == 'retrieve':
            # Heavy optimization for detail
            from .models import ActivityLog
            
            qs = qs.select_related(
                'category',
                'document_type',
                'uploaded_by',
                'approval',
                'approval__reviewed_by'
            ).prefetch_related(
                'tags',
                'permissions',
                'versions',
                Prefetch(
                    'activities',
                    queryset=ActivityLog.objects.select_related('user').order_by('-created_at')[:10]
                )
            )
        
        return qs
    
    def create(self, request, *args, **kwargs):
        """Create document and return detail representation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        
        # Return with detail serializer
        detail_serializer = DocumentDetailSerializer(document)
        return Response(
            detail_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update document and return detail representation"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        
        # Return with detail serializer
        detail_serializer = DocumentDetailSerializer(document)
        return Response(detail_serializer.data)
    
    @action(detail=True, methods=['patch'], url_path='update-file')
    def update_file(self, request, pk=None):
        """Replace document file (creates version)"""
        document = self.get_object()
        
        serializer = DocumentFileUpdateSerializer(
            document,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            DocumentDetailSerializer(document).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """
        Log download activity and return file URL.
        Actual file serving handled by web server.
        """
        from .models import ActivityLog
        
        document = self.get_object()
        
        # Check if user can download
        if not document.can_be_downloaded:
            return Response(
                {'error': 'Document cannot be downloaded'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Log activity
        document.log_activity(
            action=ActivityLog.ActionTypes.DOCUMENT_DOWNLOAD,
            user=request.user,
            description=f"Document '{document.title}' downloaded",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            'url': request.build_absolute_uri(document.file_path.url),
            'filename': document.file_path.name.split('/')[-1],
            'size': document.file_size_mb,
            'mime_type': document.mime_type
        })
    
    @action(detail=True, methods=['post'])
    def view(self, request, pk=None):
        """Log view activity and increment counter"""
        document = self.get_object()
        
        # Increment view count
        document.increment_view_count()
        
        # Log activity
        document.log_activity(
            action=ActivityLog.ActionTypes.DOCUMENT_VIEW,
            user=request.user,
            description=f"Document '{document.title}' viewed"
        )
        
        return Response({'view_count': document.view_count})
```

---

## Part 6: Testing Your Implementation

### Step 6.1: Create Test Data

```python
# In Django shell or management command
from django.contrib.auth import get_user_model
from apps.Documents.models import Category, Tag, DocumentType, Document
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

# Create user
user = User.objects.first()  # or create one

# Create categories
cat1 = Category.objects.create(name="Academic", icon="📚")
cat2 = Category.objects.create(name="Administrative", icon="📋")

# Create tags
tag1 = Tag.objects.create(name="Important")
tag2 = Tag.objects.create(name="Public")
tag3 = Tag.objects.create(name="Finance")

# Create document type
doc_type = DocumentType.objects.create(
    name="PDF Document",
    allowed_extensions=['pdf'],
    max_file_size_mb=10
)

# Create sample document
content = b"Sample PDF content"
file = SimpleUploadedFile("test.pdf", content, content_type="application/pdf")

doc = Document.objects.create(
    title="Sample Document",
    description="This is a test document",
    file_path=file,
    file_size=len(content),
    file_extension="pdf",
    category=cat1,
    document_type=doc_type,
    uploaded_by=user
)
doc.tags.set([tag1, tag2])
```

---

### Step 6.2: Test API Endpoints

```python
# Test with Django REST Framework's test client
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

# Setup
client = APIClient()
user = User.objects.first()
refresh = RefreshToken.for_user(user)
client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

# Test list endpoint
response = client.get('/api/documents/')
print(f"Status: {response.status_code}")
print(f"Count: {len(response.data['results'])}")
print(f"First document: {response.data['results'][0]['title']}")

# Test detail endpoint
doc_id = response.data['results'][0]['id']
response = client.get(f'/api/documents/{doc_id}/')
print(f"Detail response keys: {response.data.keys()}")

# Test create endpoint
with open('test.pdf', 'rb') as f:
    response = client.post('/api/documents/', {
        'title': 'New Document',
        'description': 'Test upload',
        'file_path': f,
        'category_id': cat1.id,
        'tag_ids': [tag1.id, tag2.id]
    }, format='multipart')
print(f"Create status: {response.status_code}")
```

---

### 🎯 Exercise 6: Performance Testing

**Task:** Measure and compare performance of different serializer levels

```python
import time
from django.test.utils import override_settings
from django.db import connection, reset_queries

def measure_serialization(queryset, serializer_class, many=True):
    """Measure queries and time"""
    reset_queries()
    start = time.time()
    
    serializer = serializer_class(queryset, many=many)
    data = serializer.data  # Force evaluation
    
    end = time.time()
    
    return {
        'time': end - start,
        'queries': len(connection.queries),
        'data_size': len(str(data))
    }

# Test with 50 documents
from apps.Documents.models import Document
from apps.Documents.serializers import (
    DocumentMinimalSerializer,
    DocumentListSerializer,
    DocumentDetailSerializer
)

docs = Document.objects.all()[:50]

# Test Minimal
result = measure_serialization(docs, DocumentMinimalSerializer)
print(f"Minimal: {result}")

# Test List (without optimization)
docs = Document.objects.all()[:50]
result = measure_serialization(docs, DocumentListSerializer)
print(f"List (unoptimized): {result}")

# Test List (with optimization)
docs = Document.objects.select_related('category', 'uploaded_by').prefetch_related('tags')[:50]
result = measure_serialization(docs, DocumentListSerializer)
print(f"List (optimized): {result}")

# Test Detail (single document)
doc = Document.objects.select_related('category', 'uploaded_by').prefetch_related('tags').first()
result = measure_serialization(doc, DocumentDetailSerializer, many=False)
print(f"Detail (single, optimized): {result}")
```

**Expected results:**
- Minimal: ~5-10 queries, <0.05s
- List unoptimized: 150+ queries, >1s
- List optimized: 3-5 queries, <0.1s
- Detail: 6-10 queries, <0.15s

---

## Summary & Next Steps

### ✅ What You've Learned

1. **Level 1 (Minimal):** Create lightweight serializers for references
2. **Level 2 (List):** Optimize for bulk display with proper query optimization
3. **Level 3 (Detail):** Full data with nested serializers
4. **Level 4 (Write):** Separate create/update with validation

### 🎯 Practice Exercises

1. **Create CategoryViewSet** with all 4 serializer levels
2. **Implement TagViewSet** with autocomplete endpoint
3. **Build ApprovalViewSet** with approve/reject actions
4. **Add filtering** to DocumentViewSet (by date range, file type, etc.)
5. **Create statistics endpoint** (most downloaded, recently uploaded, etc.)

### 📚 Advanced Topics to Explore

- Dynamic field selection
- Conditional nesting (expand= parameter)
- API versioning
- Caching strategies
- Pagination customization
- File upload progress tracking
- Bulk operations

### 🔗 Related Files

- Main guide: `SERIALIZER_ARCHITECTURE_GUIDE.md`
- Example code: `serializers_example.py`
- Your models: `models.py`
- Test your code: Create `tests/test_serializers.py`

---

**Remember:** Start simple, test thoroughly, and optimize based on actual usage patterns. The goal is appropriate depth for each use case, not perfection!

