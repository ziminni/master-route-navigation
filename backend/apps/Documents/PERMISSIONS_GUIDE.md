# Documents & Folders - Permission System Guide

## Overview

The system now supports **hierarchical folder organization** with **role-based and user-specific permissions**.

## User Roles & Default Permissions

### 1. **Admin**
- ✅ Full CRUD on ALL documents and folders
- ✅ Manages entire system
- ✅ Can set permissions for others
- ✅ No restrictions

### 2. **Faculty**
- ✅ Full CRUD on their own documents/folders
- ✅ View/download documents in public folders
- ❌ Cannot edit/delete others' documents
- 📝 No approval needed for uploads

### 3. **Student**
- ✅ View documents (if approved and public)
- ✅ Download documents (if approved)
- ❌ Cannot upload/edit/delete
- 📝 Read-only access

### 4. **Staff (Student Org Officer)**
- ✅ View/download documents
- ✅ Upload documents **BUT requires approval**
- ❌ Cannot edit/delete (except via admin grant)
- 📝 Uploads go to pending approval state

---

## Permission Hierarchy

```
Folder Permissions
    ↓ (inherited by)
Document Permissions
    ↓ (overridden by)
User-Specific Permissions
```

### Example:
```
Folder: /Academic/CS101/
  - Role Permission: faculty=all, student=view only
  
  Document: syllabus.pdf (in CS101 folder)
    - Inherits: students can view
    - Override: Allow student "john@edu" to edit
    
  Result: Most students view-only, but john can edit
```

---

## Models Explained

### **Folder Model**
Hierarchical folder structure:
```python
Folder(
    name="CS101",
    parent=academic_folder,  # /Academic/CS101/
    category=academic_category,
    created_by=faculty_user,
    is_public=True  # Everyone can see structure
)
```

**Key Features:**
- Unlimited nesting depth
- Soft delete (deleted_at)
- Full path tracking: `/Academic/CS101/Lectures`
- Methods: `get_full_path()`, `get_ancestors()`, `get_descendants()`

### **FolderPermission Model**
User-specific folder permissions:
```python
FolderPermission(
    folder=cs101_folder,
    user=john_student,
    can_view=True,
    can_upload=True,  # Special permission granted
    can_edit=False,
    can_delete=False
)
```

### **FolderRolePermission Model**
Role-based folder permissions:
```python
FolderRolePermission(
    folder=cs101_folder,
    role='student',
    can_view=True,
    can_upload=False,
    can_edit=False,
    can_delete=False
)
```

### **Document Model (Updated)**
Documents now belong to folders:
```python
Document(
    title="Syllabus.pdf",
    folder=cs101_folder,  # NEW FIELD
    category=academic_category,
    uploaded_by=faculty_user,
    document_type=pdf_type
)
```

### **DocumentPermission Model (Updated)**
Added `can_edit` and `can_delete` fields:
```python
DocumentPermission(
    document=syllabus_doc,
    role='student',
    can_view=True,
    can_download=True,
    can_edit=False,  # NEW
    can_delete=False  # NEW
)
```

---

## Permission Checking

### In Code:

```python
# Check folder access
if folder.can_user_access(request.user, action='upload'):
    # Allow upload
    pass

# Check document access
if document.can_user_access(request.user, action='edit'):
    # Allow edit
    pass
```

### Actions:
- `'view'` - Can see the resource
- `'download'` - Can download (documents only)
- `'upload'` - Can add new items
- `'edit'` - Can modify existing items
- `'delete'` - Can remove items

---

## Use Case Examples

### Use Case 1: Faculty Uploads Course Materials
```python
# Create folder
folder = Folder.objects.create(
    name="CS101 Spring 2025",
    category=academic_category,
    created_by=faculty_user,
    is_public=True
)

# Set role permissions
FolderRolePermission.objects.create(
    folder=folder,
    role='student',
    can_view=True,
    can_upload=False,
    can_edit=False,
    can_delete=False
)

# Upload document
document = Document.objects.create(
    title="Week1_Lecture.pdf",
    folder=folder,
    uploaded_by=faculty_user,
    file_path=uploaded_file,
    category=academic_category
)

# Result: Students can view/download, faculty can edit
```

### Use Case 2: Student Org Officer Uploads Event Poster
```python
# Staff user uploads
document = Document.objects.create(
    title="Annual Event Poster.pdf",
    folder=events_folder,
    uploaded_by=staff_user,  # role='staff'
    file_path=uploaded_file,
    document_type=requires_approval_type  # requires_approval=True
)

# Document is created but needs approval
approval = DocumentApproval.objects.create(
    document=document,
    status='pending'
)

# Admin reviews
approval.status = 'approved'
approval.reviewed_by = admin_user
approval.save()  # Auto-creates history entry

# Now document.can_be_downloaded = True
```

### Use Case 3: Private Faculty Folder
```python
# Create private folder
folder = Folder.objects.create(
    name="Internal Faculty Resources",
    category=admin_category,
    created_by=admin_user,
    is_public=False  # Not visible to students
)

# Only faculty can access
FolderRolePermission.objects.create(
    folder=folder,
    role='faculty',
    can_view=True,
    can_upload=True,
    can_edit=True,
    can_delete=False
)

# Students won't see this folder at all
student.can_user_access(folder, 'view')  # False
```

### Use Case 4: Grant Special Student Access
```python
# John is a student assistant
FolderPermission.objects.create(
    folder=faculty_folder,
    user=john_student,
    can_view=True,
    can_upload=True,  # Can help upload
    can_edit=True,    # Can organize files
    can_delete=False  # But not delete
)

# John gets elevated permissions despite being 'student' role
```

---

## API Implementation Example

### views.py
```python
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied

class FolderViewSet(viewsets.ModelViewSet):
    queryset = Folder.objects.filter(deleted_at__isnull=True)
    serializer_class = FolderSerializer
    
    def get_queryset(self):
        """Filter folders user can access"""
        user = self.request.user
        if user.role_type == 'admin':
            return self.queryset
        
        # Get folders user has permissions for
        accessible = []
        for folder in self.queryset:
            if folder.can_user_access(user, 'view'):
                accessible.append(folder.id)
        
        return self.queryset.filter(id__in=accessible)
    
    def perform_create(self, serializer):
        """Check upload permission"""
        parent = serializer.validated_data.get('parent')
        
        if parent and not parent.can_user_access(self.request.user, 'upload'):
            raise PermissionDenied("Cannot create folder here")
        
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def contents(self, request, pk=None):
        """List folder contents (subfolders + documents)"""
        folder = self.get_object()
        
        if not folder.can_user_access(request.user, 'view'):
            raise PermissionDenied("Cannot access this folder")
        
        # Get accessible subfolders
        subfolders = [
            f for f in folder.subfolders.filter(deleted_at__isnull=True)
            if f.can_user_access(request.user, 'view')
        ]
        
        # Get accessible documents
        documents = [
            d for d in folder.documents.filter(deleted_at__isnull=True)
            if d.can_user_access(request.user, 'view')
        ]
        
        return Response({
            'subfolders': FolderSerializer(subfolders, many=True).data,
            'documents': DocumentSerializer(documents, many=True).data
        })

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.active.all()
    serializer_class = DocumentSerializer
    
    def perform_create(self, serializer):
        """Handle document upload with approval logic"""
        user = self.request.user
        folder = serializer.validated_data.get('folder')
        
        # Check folder upload permission
        if folder and not folder.can_user_access(user, 'upload'):
            raise PermissionDenied("Cannot upload to this folder")
        
        # Save document
        document = serializer.save(uploaded_by=user)
        
        # Create approval if needed
        if user.role_type == 'staff':  # Org officer needs approval
            DocumentApproval.objects.create(
                document=document,
                status='pending'
            )
            # Log activity
            document.log_activity(
                action=ActivityLog.ActionTypes.APPROVAL_SUBMIT,
                user=user,
                description=f"Submitted {document.title} for approval"
            )
    
    def perform_update(self, serializer):
        """Check edit permission"""
        if not self.get_object().can_user_access(self.request.user, 'edit'):
            raise PermissionDenied("Cannot edit this document")
        serializer.save()
    
    def perform_destroy(self, instance):
        """Soft delete with permission check"""
        if not instance.can_user_access(self.request.user, 'delete'):
            raise PermissionDenied("Cannot delete this document")
        
        # Soft delete
        from django.utils import timezone
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user
        instance.save()
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download document"""
        document = self.get_object()
        
        if not document.can_user_access(request.user, 'download'):
            raise PermissionDenied("Cannot download this document")
        
        # Log download
        document.log_activity(
            action=ActivityLog.ActionTypes.DOCUMENT_DOWNLOAD,
            user=request.user,
            description=f"Downloaded {document.title}",
            ip=request.META.get('REMOTE_ADDR')
        )
        
        # Return file response
        # ... file serving logic
```

---

## Migration Steps

1. **Create migrations:**
```bash
python manage.py makemigrations Documents
```

2. **Review migration** - Will create:
   - `folders` table
   - `folder_permissions` table
   - `folder_role_permissions` table
   - Add `folder_id` to `documents` table
   - Add `can_edit`, `can_delete` to `document_permissions`

3. **Run migration:**
```bash
python manage.py migrate Documents
```

4. **Create initial folder structure:**
```python
# management/commands/setup_folders.py
from django.core.management.base import BaseCommand
from apps.Documents.models import Folder, Category, FolderRolePermission

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Create root folders for each category
        academic = Category.objects.get(slug='academic')
        
        root_folder = Folder.objects.create(
            name="Academic Resources",
            category=academic,
            is_public=True
        )
        
        # Set default role permissions
        FolderRolePermission.objects.create(
            folder=root_folder,
            role='student',
            can_view=True,
            can_upload=False,
            can_edit=False,
            can_delete=False
        )
        
        self.stdout.write("Folders created!")
```

---

## Testing Checklist

- [ ] Admin can create/edit/delete any folder/document
- [ ] Faculty can create folders and upload documents
- [ ] Faculty can edit/delete only their own documents
- [ ] Students can view/download approved documents
- [ ] Students cannot upload/edit/delete
- [ ] Staff uploads require approval
- [ ] Folder permissions inherit to documents
- [ ] User-specific permissions override role permissions
- [ ] Private folders not visible to unauthorized users
- [ ] Soft delete works for folders and documents
- [ ] Activity logs track all actions
- [ ] Approval workflow validates transitions

---

## Best Practices

1. **Always check permissions in views:**
   ```python
   if not obj.can_user_access(request.user, action):
       raise PermissionDenied()
   ```

2. **Use folder permissions for broad access control**
3. **Use document permissions for specific exceptions**
4. **Log important actions** (uploads, downloads, approvals)
5. **Soft delete instead of hard delete** (preserves history)
6. **Set requires_approval=True** for DocumentTypes that need review

---

## Security Considerations

1. **Never trust client-side checks** - Always validate server-side
2. **Log sensitive operations** - Downloads, deletions, permission changes
3. **Use HTTPS** for file uploads/downloads
4. **Validate file types** - Check mime_type and extension
5. **Scan uploads for malware** - Consider ClamAV integration
6. **Rate limit downloads** - Prevent abuse
7. **Audit permission changes** - Who granted what to whom

---

## Future Enhancements

- [ ] Folder templates (auto-create structure)
- [ ] Bulk permission management
- [ ] Share links (temporary access tokens)
- [ ] Folder/document starring/favorites
- [ ] Advanced search with folder filtering
- [ ] Storage quota per user/role
- [ ] Expiring documents (auto-delete after date)
- [ ] Document co-ownership (multiple uploaders)
