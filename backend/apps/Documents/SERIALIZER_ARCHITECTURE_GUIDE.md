# 📚 Hierarchical Serializer Architecture - Complete Guide

## Table of Contents
1. [Core Concepts](#core-concepts)
2. [The Four Levels](#the-four-levels)
3. [Deep Dive: Each Level](#deep-dive-each-level)
4. [Real-World Examples](#real-world-examples)
5. [Performance Impact](#performance-impact)
6. [When to Use What](#when-to-use-what)
7. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
8. [Advanced Patterns](#advanced-patterns)

---

## Core Concepts

### What is Hierarchical Organization?

**Hierarchical Organization** is a design pattern where you create multiple serializers for the same model, each serving a different purpose based on the **depth of data** and **use case**.

### Why Not Just One Serializer Per Model?

```python
# ❌ BAD: One serializer doing everything
class DocumentSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    tags = TagSerializer(many=True)
    uploaded_by = UserSerializer()
    permissions = PermissionSerializer(many=True)
    versions = VersionSerializer(many=True)
    activities = ActivitySerializer(many=True)
    approval = ApprovalSerializer()
    
    class Meta:
        model = Document
        fields = '__all__'  # Everything!
```

**Problems:**
- 🐌 **Slow**: Loads tons of data even when listing 100 documents
- 💾 **Memory intensive**: Each document carries nested objects
- 🔄 **N+1 queries**: Without proper optimization, causes database explosion
- 🚫 **Not reusable**: Can't use for different contexts
- 📦 **Large payload**: 10KB per document when you need 500 bytes

**Instead, we create a hierarchy:**

```python
# ✅ GOOD: Multiple specialized serializers
DocumentMinimalSerializer     # 50 bytes  - For dropdowns
DocumentListSerializer        # 500 bytes - For browsing
DocumentDetailSerializer      # 5KB      - For full view
DocumentWriteSerializer       # N/A      - For create/update
```

---

## The Four Levels

### Visual Hierarchy

```
📊 Data Depth vs Use Case

Level 1: Minimal     [====]               5 fields    Dropdowns, FK displays
Level 2: List        [==========]         10 fields   Tables, cards, search
Level 3: Detail      [===================] 20+ fields Full page view
Level 4: Write       [=========]          Varies      Form submission
                     
                     ← Less Data                    More Data →
                     ← Faster                        Slower →
                     ← Many instances                One instance →
```

---

## Deep Dive: Each Level

### 🔹 LEVEL 1: Minimal Serializers

**Purpose:** Represent a model with just enough info for identification

**Characteristics:**
- 2-5 fields maximum
- Only essential display data
- No nested objects
- No computed fields (unless very cheap)
- Used inside other serializers

**When to use:**
- As nested fields in other serializers
- For dropdown/select options
- As foreign key representations
- In list views where space is limited

**Example Pattern:**

```python
class CategoryMinimalSerializer(serializers.ModelSerializer):
    """Minimal category - just enough to display"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon']
        read_only_fields = fields  # All read-only


class TagMinimalSerializer(serializers.ModelSerializer):
    """Minimal tag - for document tags display"""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']
        read_only_fields = fields
```

**Usage:**
```python
# ✅ Inside another serializer
class DocumentListSerializer(serializers.ModelSerializer):
    tags = TagMinimalSerializer(many=True, read_only=True)
    # Now each document has compact tag info: [{id: 1, name: "Finance", slug: "finance"}]
```

**Performance Impact:**
```
Without optimization:
  Document list: 100 docs × 5 tags each = 500 tag queries 💥

With minimal serializer + prefetch_related:
  Document.objects.prefetch_related('tags')
  Result: 2 queries total (1 for docs, 1 for all tags) ✅
```

---

### 🔹 LEVEL 2: List Serializers

**Purpose:** Display multiple objects efficiently in lists, tables, cards

**Characteristics:**
- 8-15 fields typically
- Mix of direct fields + 1-2 simple computed fields
- May include **one level** of nested minimal serializers
- Optimized for bulk display (100+ instances)
- No expensive operations

**When to use:**
- Browse/search results pages
- Data tables
- Card grids
- Dashboard widgets
- API list endpoints

**Example Pattern:**

```python
class DocumentListSerializer(serializers.ModelSerializer):
    """For document library browsing"""
    
    # Simple direct field access
    category_name = serializers.CharField(
        source='category.name', 
        read_only=True
    )
    
    # Computed property from model
    file_size_mb = serializers.ReadOnlyField()
    
    # Nested minimal serializer (1 level only!)
    tags = TagMinimalSerializer(many=True, read_only=True)
    
    # SerializerMethodField for custom logic
    uploaded_by_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description',
            'category_name',           # Not full category object
            'file_size_mb',            # Computed
            'file_extension',
            'uploaded_at',
            'view_count',
            'is_featured',
            'tags',                    # Only minimal info
            'uploaded_by_display'      # Custom format
        ]
        read_only_fields = [
            'uploaded_at', 'view_count', 'file_size_mb'
        ]
    
    def get_uploaded_by_display(self, obj):
        """Format: 'John D.' instead of full user object"""
        if obj.uploaded_by:
            return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name[0]}."
        return "Unknown"
```

**ViewSet Usage:**

```python
class DocumentViewSet(viewsets.ModelViewSet):
    
    def list(self, request):
        # Optimize queries for list view
        queryset = Document.active.select_related(
            'category',           # ForeignKey - use select_related
            'uploaded_by'
        ).prefetch_related(
            'tags'                # ManyToMany - use prefetch_related
        )
        
        serializer = DocumentListSerializer(queryset, many=True)
        return Response(serializer.data)
```

**Query Optimization:**

```python
# ❌ Without optimization
Document.objects.all()  # 100 documents
# Each document access:
#   - document.category.name    → 100 queries
#   - document.uploaded_by.name → 100 queries  
#   - document.tags.all()       → 100 queries
# Total: 1 + 300 = 301 queries! 💥

# ✅ With optimization
Document.objects.select_related('category', 'uploaded_by').prefetch_related('tags')
# Total: 3 queries (docs, categories+users in 1 join, tags in 1 query) ✅
```

---

### 🔹 LEVEL 3: Detail Serializers

**Purpose:** Full representation of a single object with all related data

**Characteristics:**
- 20-40+ fields
- Multiple nested serializers (use List serializers, not Detail!)
- Computed properties
- Related counts/statistics
- Multiple SerializerMethodFields
- Designed for **single instance** retrieval

**When to use:**
- Detail/view pages
- Edit forms (pre-populated)
- Full object API endpoints
- When user needs complete information

**Example Pattern:**

```python
class DocumentDetailSerializer(serializers.ModelSerializer):
    """Complete document information"""
    
    # Nested LIST serializers (not Minimal, not Detail!)
    category = CategoryListSerializer(read_only=True)
    document_type = DocumentTypeListSerializer(read_only=True)
    uploaded_by = UserListSerializer(read_only=True)
    tags = TagListSerializer(many=True, read_only=True)
    
    # Related objects (reverse relations)
    permissions = DocumentPermissionSerializer(many=True, read_only=True)
    approval = DocumentApprovalSerializer(read_only=True)
    
    # Computed properties from model
    file_size_mb = serializers.ReadOnlyField()
    can_be_downloaded = serializers.ReadOnlyField()
    download_count = serializers.ReadOnlyField()
    
    # Complex computed fields
    recent_activities = serializers.SerializerMethodField()
    version_info = serializers.SerializerMethodField()
    permission_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            # Basic info
            'id', 'title', 'description',
            
            # File info
            'file_path', 'file_size', 'file_size_mb',
            'file_extension', 'mime_type',
            
            # Relations (full objects)
            'category', 'document_type', 'uploaded_by', 'tags',
            
            # Reverse relations
            'permissions', 'approval',
            
            # Timestamps
            'uploaded_at', 'updated_at',
            
            # Status
            'is_active', 'is_featured',
            
            # Computed
            'view_count', 'download_count', 'can_be_downloaded',
            
            # Complex computed
            'recent_activities', 'version_info', 'permission_summary'
        ]
    
    def get_recent_activities(self, obj):
        """Last 10 activities"""
        activities = obj.activities.select_related('user').order_by('-created_at')[:10]
        return ActivityLogSerializer(activities, many=True).data
    
    def get_version_info(self, obj):
        """Version information"""
        current_version = obj.versions.filter(is_current=True).first()
        total_versions = obj.versions.count()
        
        return {
            'current_version': current_version.version_number if current_version else 1,
            'total_versions': total_versions,
            'has_versions': total_versions > 1
        }
    
    def get_permission_summary(self, obj):
        """Summarize who can access"""
        perms = obj.permissions.all()
        return {
            'roles_with_access': [p.role for p in perms if p.can_view],
            'roles_can_download': [p.role for p in perms if p.can_download],
            'is_public': perms.filter(role='student', can_view=True).exists()
        }
```

**Important: Why nested LIST serializers?**

```python
# ❌ DON'T nest Detail serializers
class DocumentDetailSerializer(serializers.ModelSerializer):
    category = CategoryDetailSerializer()  # ❌ Too deep!
    # Now you're loading category + category's documents + those documents' categories... 
    # = Circular nightmare

# ✅ DO nest List serializers  
class DocumentDetailSerializer(serializers.ModelSerializer):
    category = CategoryListSerializer()  # ✅ Just enough info
    # Category shows: id, name, slug, icon, document_count
    # Doesn't load all category's documents
```

**ViewSet Usage:**

```python
class DocumentViewSet(viewsets.ModelViewSet):
    
    def retrieve(self, request, pk=None):
        # Optimize for single object with all relations
        document = Document.objects.select_related(
            'category',
            'document_type', 
            'uploaded_by',
            'approval',
            'approval__reviewed_by'
        ).prefetch_related(
            'tags',
            'permissions',
            'versions',
            'activities__user'
        ).get(pk=pk)
        
        serializer = DocumentDetailSerializer(document)
        return Response(serializer.data)
```

---

### 🔹 LEVEL 4: Write Serializers

**Purpose:** Handle create, update, and complex write operations

**Characteristics:**
- Different fields than read serializers
- Validation logic
- Write-only fields
- Custom create()/update() methods
- File upload handling
- Business logic enforcement

**When to use:**
- POST/PUT/PATCH endpoints
- Form submissions
- File uploads
- State transitions (approve, publish, etc.)

**Why separate from read serializers?**

1. **Different field requirements**
   - Write: `category_id` (integer)
   - Read: `category` (full object)

2. **Validation logic**
   - File size checks
   - Extension validation
   - Business rules

3. **Security**
   - Write-only sensitive fields
   - Computed fields aren't writable

4. **File handling**
   - Special processing for uploads
   - Version creation

**Example Pattern:**

```python
class DocumentCreateSerializer(serializers.ModelSerializer):
    """For uploading new documents"""
    
    # Write-only fields (IDs, not objects)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
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
    
    # File field
    file_path = serializers.FileField()
    
    class Meta:
        model = Document
        fields = [
            'title', 'description',
            'file_path',
            'category_id',           # Not 'category'
            'document_type_id',      # Not 'document_type'
            'tag_ids',               # Not 'tags'
            'is_featured'
        ]
    
    def validate_file_path(self, value):
        """Validate uploaded file"""
        # Check file size
        if value.size > 100 * 1024 * 1024:  # 100MB
            raise serializers.ValidationError("File too large (max 100MB)")
        
        # Check extension
        ext = value.name.split('.')[-1].lower()
        allowed = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']
        if ext not in allowed:
            raise serializers.ValidationError(
                f"File type '.{ext}' not allowed. Allowed: {', '.join(allowed)}"
            )
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        document_type = attrs.get('document_type')
        file_path = attrs.get('file_path')
        
        if document_type and file_path:
            # Check against document type rules
            ext = file_path.name.split('.')[-1].lower()
            
            if document_type.allowed_extensions:
                if ext not in document_type.allowed_extensions:
                    raise serializers.ValidationError({
                        'file_path': f"File type not allowed for {document_type.name}"
                    })
            
            # Check size against document type max
            max_size = document_type.max_file_size_mb * 1024 * 1024
            if file_path.size > max_size:
                raise serializers.ValidationError({
                    'file_path': f"File exceeds max size for {document_type.name} "
                                f"({document_type.max_file_size_mb}MB)"
                })
        
        return attrs
    
    def create(self, validated_data):
        """Custom create logic"""
        # Extract many-to-many (can't set on unsaved instance)
        tag_ids = validated_data.pop('tag_ids', [])
        
        # Set uploaded_by from request context
        request = self.context.get('request')
        validated_data['uploaded_by'] = request.user
        
        # Extract file metadata
        file_obj = validated_data.get('file_path')
        if file_obj:
            validated_data['file_size'] = file_obj.size
            validated_data['file_extension'] = file_obj.name.split('.')[-1].lower()
            
            # You might use python-magic for accurate mime type
            # import magic
            # validated_data['mime_type'] = magic.from_buffer(
            #     file_obj.read(1024), 
            #     mime=True
            # )
        
        # Create document
        document = Document.objects.create(**validated_data)
        
        # Set tags (many-to-many)
        if tag_ids:
            document.tags.set(tag_ids)
        
        # Create approval if document type requires it
        if document.document_type and document.document_type.requires_approval:
            DocumentApproval.objects.create(
                document=document,
                status='pending'
            )
        
        # Log activity (or handled by signal)
        document.log_activity(
            action=ActivityLog.ActionTypes.DOCUMENT_UPLOAD,
            user=request.user,
            description=f"Document '{document.title}' uploaded"
        )
        
        return document


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """For updating document metadata (not file)"""
    
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
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
            'title', 'description',
            'category_id', 'tag_ids',
            'is_featured', 'is_active'
        ]
    
    def update(self, instance, validated_data):
        """Custom update logic"""
        tag_ids = validated_data.pop('tag_ids', None)
        
        # Update regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update tags if provided
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        
        # Log activity
        request = self.context.get('request')
        instance.log_activity(
            action=ActivityLog.ActionTypes.DOCUMENT_UPDATE,
            user=request.user,
            description=f"Document '{instance.title}' updated"
        )
        
        return instance


class DocumentFileUpdateSerializer(serializers.ModelSerializer):
    """For replacing document file (creates new version)"""
    
    file_path = serializers.FileField()
    change_notes = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Document
        fields = ['file_path', 'change_notes']
    
    def validate_file_path(self, value):
        """Same validation as create"""
        # ... validation logic ...
        return value
    
    def update(self, instance, validated_data):
        """Create version, then update document"""
        change_notes = validated_data.pop('change_notes', '')
        request = self.context.get('request')
        
        # Create new version from current file
        latest_version = instance.versions.order_by('-version_number').first()
        new_version_number = (latest_version.version_number + 1) if latest_version else 1
        
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
            change_notes="Previous version before update",
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
            version=new_version_number
        )
        
        return instance
```

**ViewSet Usage:**

```python
class DocumentViewSet(viewsets.ModelViewSet):
    
    def get_serializer_class(self):
        """Different serializers for different actions"""
        if self.action == 'list':
            return DocumentListSerializer
        elif self.action == 'retrieve':
            return DocumentDetailSerializer
        elif self.action == 'create':
            return DocumentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DocumentUpdateSerializer
        return DocumentDetailSerializer
    
    def create(self, request):
        serializer = DocumentCreateSerializer(
            data=request.data,
            context={'request': request}  # Pass request for user access
        )
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        
        # Return with detail serializer
        return Response(
            DocumentDetailSerializer(document).data,
            status=status.HTTP_201_CREATED
        )
    
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
        
        return Response(DocumentDetailSerializer(document).data)
```

---

## Real-World Examples

### Example 1: Document Library Page

**Frontend needs:**
- List 50 documents per page
- Show title, category, file size, upload date, tags
- Filter by category, type
- Search by title

**Solution:**

```python
# ViewSet
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.active.all()
    serializer_class = DocumentListSerializer  # ← Level 2
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'document_type', 'is_featured']
    search_fields = ['title', 'description']
    ordering_fields = ['uploaded_at', 'title', 'view_count']
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'category', 'uploaded_by'
        ).prefetch_related('tags')

# API Call: GET /api/documents/?category=5&search=budget
# Response: 50 documents, ~25KB total, 3 DB queries
```

---

### Example 2: Document Detail Modal

**Frontend needs:**
- Full document info
- Category details
- All tags
- Permission info
- Download button (check can_be_downloaded)
- Recent activity log

**Solution:**

```python
class DocumentViewSet(viewsets.ModelViewSet):
    
    def retrieve(self, request, pk=None):
        document = self.get_queryset().select_related(
            'category',
            'document_type',
            'uploaded_by',
            'approval__reviewed_by'
        ).prefetch_related(
            'tags',
            'permissions',
            'activities__user'
        ).get(pk=pk)
        
        serializer = DocumentDetailSerializer(document)  # ← Level 3
        return Response(serializer.data)

# API Call: GET /api/documents/42/
# Response: 1 document, ~8KB, 6 DB queries
```

---

### Example 3: Upload New Document Form

**Frontend needs:**
- Upload file
- Select category (dropdown)
- Enter title, description
- Select document type (dropdown)
- Choose tags (multi-select)

**Solution:**

```python
# Get form options
GET /api/categories/              # → CategoryMinimalSerializer (Level 1)
GET /api/document-types/          # → DocumentTypeMinimalSerializer (Level 1)
GET /api/tags/                    # → TagMinimalSerializer (Level 1)

# Submit form
POST /api/documents/              # → DocumentCreateSerializer (Level 4)
{
    "title": "Q4 Budget Report",
    "description": "Financial summary...",
    "file_path": <file>,
    "category_id": 5,
    "document_type_id": 2,
    "tag_ids": [1, 3, 7]
}

# Response: Full document (Level 3 serializer)
```

---

### Example 4: Approval Workflow

**Frontend needs:**
- List pending approvals
- View document + approval status
- Approve or reject with notes

**Solution:**

```python
# Specialized serializers for approval workflow

class PendingApprovalListSerializer(serializers.ModelSerializer):
    """For approval dashboard"""
    document = DocumentListSerializer(read_only=True)  # Level 2 nested
    
    class Meta:
        model = DocumentApproval
        fields = ['id', 'document', 'status', 'submitted_at', 
                  'resubmission_count']


class ApprovalActionSerializer(serializers.Serializer):
    """For approve/reject action"""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    notes = serializers.CharField(required=False)
    
    def validate(self, attrs):
        approval = self.context['approval']
        if approval.status != 'pending':
            raise serializers.ValidationError(
                "Can only approve/reject pending documents"
            )
        return attrs
    
    def save(self):
        approval = self.context['approval']
        request = self.context['request']
        action = self.validated_data['action']
        notes = self.validated_data.get('notes', '')
        
        # Save previous status
        approval.previous_status = approval.status
        
        # Update status
        if action == 'approve':
            approval.status = 'approved'
        else:
            approval.status = 'rejected'
        
        approval.reviewed_by = request.user
        approval.reviewed_at = timezone.now()
        approval.review_notes = notes
        approval.save()
        
        # Create history entry
        ApprovalHistory.objects.create(
            approval=approval,
            status_from=approval.previous_status,
            status_to=approval.status,
            changed_by=request.user,
            notes=notes
        )
        
        # Log activity
        approval.log_activity(
            action=ActivityLog.ActionTypes.APPROVAL_APPROVE if action == 'approve' 
                   else ActivityLog.ActionTypes.APPROVAL_REJECT,
            user=request.user,
            description=f"Document {action}d"
        )
        
        return approval


# ViewSet
class DocumentApprovalViewSet(viewsets.ModelViewSet):
    
    @action(detail=True, methods=['post'])
    def approve_reject(self, request, pk=None):
        approval = self.get_object()
        
        serializer = ApprovalActionSerializer(
            data=request.data,
            context={'approval': approval, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        updated_approval = serializer.save()
        
        return Response(
            DocumentApprovalSerializer(updated_approval).data
        )
```

---

## Performance Impact

### Benchmark Comparison

**Scenario:** Load 100 documents

| Serializer Level | Payload Size | DB Queries | Response Time | Use Case |
|-----------------|--------------|------------|---------------|----------|
| Detail (wrong!) | 800 KB | 1,500+ | 3,500ms | ❌ Never for lists |
| List (optimized) | 50 KB | 3 | 85ms | ✅ Browsing |
| Minimal | 5 KB | 1 | 15ms | ✅ Dropdowns |

**Analysis:**

```python
# ❌ BAD: Using Detail serializer for list
GET /api/documents/
# Response: 100 documents × 8KB each = 800KB
# Queries: 
#   - 100 for each document's category details
#   - 100 for each document's tags
#   - 100 for each document's permissions
#   - 100 for each document's activities
#   - 100 for each document's versions
# Total: 501+ queries, 3.5 seconds

# ✅ GOOD: Using List serializer
GET /api/documents/
# Response: 100 documents × 500 bytes = 50KB
# Queries:
#   - 1 for documents
#   - 1 for categories (select_related)
#   - 1 for tags (prefetch_related)
# Total: 3 queries, 85ms
```

### Query Optimization Strategies

```python
class DocumentViewSet(viewsets.ModelViewSet):
    
    def get_queryset(self):
        qs = Document.active.all()
        
        # Optimize based on action
        if self.action == 'list':
            # Level 2: Light optimization
            return qs.select_related(
                'category',           # ForeignKey
                'uploaded_by'         # ForeignKey
            ).prefetch_related(
                'tags'                # ManyToMany
            )
        
        elif self.action == 'retrieve':
            # Level 3: Heavy optimization
            return qs.select_related(
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
```

---

## When to Use What

### Decision Tree

```
Need to serialize Document?
│
├─ For dropdown/select?
│  └─ Use: DocumentMinimalSerializer (Level 1)
│     Fields: id, title
│
├─ For list/table/cards?
│  └─ Use: DocumentListSerializer (Level 2)
│     Instances: Many (10-100+)
│     Optimize: select_related + prefetch_related
│
├─ For detail page?
│  └─ Use: DocumentDetailSerializer (Level 3)
│     Instances: One
│     Include: All relations, computed fields
│
└─ For form submission?
   └─ Use: DocumentWriteSerializer (Level 4)
      Purpose: Create/Update with validation
```

### Matrix

| Use Case | Serializer Level | Typical Count | Optimization | Response Size |
|----------|------------------|---------------|--------------|---------------|
| Dropdown options | Minimal (1) | 10-50 | None needed | 1-5 KB |
| Search autocomplete | Minimal (1) | 5-20 | None needed | <1 KB |
| Table/Grid view | List (2) | 20-100 | select/prefetch | 20-100 KB |
| Card layout | List (2) | 10-50 | select/prefetch | 10-50 KB |
| Detail modal | Detail (3) | 1 | Heavy prefetch | 5-15 KB |
| Edit form | Detail (3) | 1 | Heavy prefetch | 5-15 KB |
| Form submit | Write (4) | 1 | N/A (write) | Varies |
| Nested field | Minimal/List | N/A | Parent's prefetch | N/A |

---

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Nesting Detail in Detail

```python
# ❌ BAD: Recursive nightmare
class DocumentDetailSerializer(serializers.ModelSerializer):
    category = CategoryDetailSerializer()  # Category loads all its documents
    # Each document loads its category
    # Each category loads its documents
    # Each document loads its category...
    # = INFINITE RECURSION or massive data
```

**Solution:**
```python
# ✅ GOOD: Nest List serializers only
class DocumentDetailSerializer(serializers.ModelSerializer):
    category = CategoryListSerializer()  # Just category info, no documents
```

---

### ❌ Anti-Pattern 2: Single Serializer for Everything

```python
# ❌ BAD: One serializer, many contexts
class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'

# Used everywhere:
DocumentSerializer(many_documents)  # Slow!
DocumentSerializer(one_document)    # Overkill!
```

**Solution:**
```python
# ✅ GOOD: Specialized serializers
if listing_many:
    DocumentListSerializer(many_documents)
elif viewing_one:
    DocumentDetailSerializer(one_document)
elif creating:
    DocumentCreateSerializer(data=request.data)
```

---

### ❌ Anti-Pattern 3: Including Activity Logs in Detail

```python
# ❌ BAD: Activities in main serializer
class DocumentDetailSerializer(serializers.ModelSerializer):
    activities = ActivityLogSerializer(many=True)  # Could be 1000+ records!
    
# Response: 50KB document + 500KB activities = 550KB
```

**Solution:**
```python
# ✅ GOOD: Separate endpoint for activities
class DocumentDetailSerializer(serializers.ModelSerializer):
    recent_activities = serializers.SerializerMethodField()
    
    def get_recent_activities(self, obj):
        return ActivityLogSerializer(
            obj.activities.all()[:10],  # Only recent 10
            many=True
        ).data

# For full activities:
GET /api/documents/42/activities/?page=1
```

---

### ❌ Anti-Pattern 4: Same Serializer for Read and Write

```python
# ❌ BAD: Confusing read/write mix
class DocumentSerializer(serializers.ModelSerializer):
    category = CategorySerializer()  # For reading (object)
    # But how to write? category = {"name": "..."}? or category_id = 5?
```

**Solution:**
```python
# ✅ GOOD: Separate serializers
class DocumentReadSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

class DocumentWriteSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category'
    )
```

---

### ❌ Anti-Pattern 5: Computed Fields Without Optimization

```python
# ❌ BAD: N+1 in SerializerMethodField
class DocumentListSerializer(serializers.ModelSerializer):
    permission_count = serializers.SerializerMethodField()
    
    def get_permission_count(self, obj):
        return obj.permissions.count()  # Query for EACH document!

# 100 documents = 100 permission queries
```

**Solution:**
```python
# ✅ GOOD: Annotate in queryset
from django.db.models import Count

queryset = Document.objects.annotate(
    permission_count=Count('permissions')
)

class DocumentListSerializer(serializers.ModelSerializer):
    permission_count = serializers.IntegerField(read_only=True)
    # No SerializerMethodField needed!
```

---

## Advanced Patterns

### Pattern 1: Dynamic Field Selection

Allow clients to request only needed fields:

```python
class DynamicFieldsSerializer(serializers.ModelSerializer):
    """
    A serializer that takes an additional `fields` argument to
    control which fields should be displayed.
    """
    
    def __init__(self, *args, **kwargs):
        # Get fields from context
        fields = self.context.get('fields')
        
        # Instantiate
        super().__init__(*args, **kwargs)
        
        if fields:
            # Drop fields not specified
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class DocumentListSerializer(DynamicFieldsSerializer):
    # ... normal definition ...
    pass


# Usage in view
GET /api/documents/?fields=id,title,category_name
# Returns only those 3 fields

# In ViewSet
def list(self, request):
    queryset = self.get_queryset()
    
    # Get requested fields
    fields = request.query_params.get('fields', '').split(',')
    
    serializer = DocumentListSerializer(
        queryset,
        many=True,
        context={'fields': fields if fields[0] else None}
    )
    return Response(serializer.data)
```

---

### Pattern 2: Conditional Nested Serialization

```python
class DocumentListSerializer(serializers.ModelSerializer):
    # Simple by default
    category_name = serializers.CharField(source='category.name')
    
    # Full object if requested
    category_detail = serializers.SerializerMethodField()
    
    def get_category_detail(self, obj):
        # Only include if requested
        if self.context.get('expand_category'):
            return CategoryListSerializer(obj.category).data
        return None


# Usage
GET /api/documents/                    # category_name only
GET /api/documents/?expand=category    # category_detail included
```

---

### Pattern 3: Shared Base Serializers

```python
class DocumentBaseSerializer(serializers.ModelSerializer):
    """Shared fields for all Document serializers"""
    file_size_mb = serializers.ReadOnlyField()
    
    class Meta:
        model = Document
        fields = ['id', 'title', 'uploaded_at', 'file_size_mb']


class DocumentListSerializer(DocumentBaseSerializer):
    """Extends base with list-specific fields"""
    category_name = serializers.CharField(source='category.name')
    
    class Meta(DocumentBaseSerializer.Meta):
        fields = DocumentBaseSerializer.Meta.fields + [
            'category_name', 'is_featured'
        ]


class DocumentDetailSerializer(DocumentBaseSerializer):
    """Extends base with detail-specific fields"""
    category = CategoryListSerializer()
    
    class Meta(DocumentBaseSerializer.Meta):
        fields = DocumentBaseSerializer.Meta.fields + [
            'description', 'category', 'tags', 'permissions'
        ]
```

---

### Pattern 4: Serializer Factories

```python
def document_serializer_factory(level='list', context=None):
    """
    Factory function to get appropriate serializer
    """
    serializers_map = {
        'minimal': DocumentMinimalSerializer,
        'list': DocumentListSerializer,
        'detail': DocumentDetailSerializer,
        'create': DocumentCreateSerializer,
        'update': DocumentUpdateSerializer,
    }
    
    serializer_class = serializers_map.get(level, DocumentListSerializer)
    
    if context:
        return serializer_class(context=context)
    return serializer_class


# Usage
serializer = document_serializer_factory('list')
data = serializer(documents, many=True).data
```

---

## Summary Cheat Sheet

### Quick Reference

```python
# LEVEL 1: Minimal - Dropdowns, FK displays
class XMinimalSerializer:
    fields = ['id', 'name']  # 2-5 fields max
    
# LEVEL 2: List - Tables, cards, browsing
class XListSerializer:
    fields = [basic + computed]  # 8-15 fields
    nested = MinimalSerializers  # 1 level only
    optimization = 'select/prefetch required'
    
# LEVEL 3: Detail - Full view, single object
class XDetailSerializer:
    fields = [all + relations + computed]  # 20+ fields
    nested = ListSerializers  # NOT Detail!
    optimization = 'heavy prefetch'
    
# LEVEL 4: Write - Create/update operations
class XWriteSerializer:
    fields = [write_only + validation]
    methods = ['create()', 'update()', 'validate()']
    purpose = 'business logic'
```

### The Golden Rules

1. **Never nest Detail in Detail** - Use List serializers for nesting
2. **Optimize queries per level** - select_related for list, heavy prefetch for detail
3. **Separate read and write** - Different validation, different fields
4. **Use minimal for nested** - Reduce payload size
5. **One serializer ≠ one model** - Create specialized versions
6. **Computed fields are expensive** - Annotate in queryset when possible
7. **Test with realistic data** - 100+ records, not 5
8. **Profile your APIs** - Django Debug Toolbar is your friend

---

## Next Steps

1. **Study your Users serializers** - You already have good patterns there
2. **Start with Category/Tag** - Simple models to practice on
3. **Build Document serializers** - Apply all 4 levels
4. **Add to ViewSets** - Implement action-based serializer selection
5. **Test performance** - Use Django Debug Toolbar
6. **Iterate** - Adjust based on actual usage patterns

---

**Remember:** The goal is not perfection, but **appropriate depth for each use case**. Start simple, measure, then optimize where needed.

