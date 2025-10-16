# Document Controller

## Overview
The Document Controller separates business logic from UI components, making the code more maintainable and reusable across different user dashboards (Admin, Student, Faculty, Staff).

## Architecture

```
┌─────────────────────┐
│   UI Components     │  (AdminDash, UserDash, CollectionView, etc.)
│  (Views/Widgets)    │
└──────────┬──────────┘
           │
           │ Uses
           ▼
┌─────────────────────┐
│ DocumentController  │  (Business Logic Layer)
└──────────┬──────────┘
           │
           │ Uses
           ▼
┌─────────────────────┐
│  Data Layer         │  (Mock JSON / Future: API calls)
│ (data_loader.py)    │
└─────────────────────┘
```

## Features

### ✅ **Implemented**

#### File Operations
- ✅ `get_files()` - Get files with role-based filtering
- ✅ `get_deleted_files()` - Get soft-deleted files
- ✅ `delete_file()` - Soft delete (moves to deleted_files)
- ✅ `restore_file()` - Restore from deleted_files
- ✅ `permanent_delete_file()` - Permanently delete file
- ✅ `upload_file()` - Upload new file with metadata
- ✅ `get_file_details()` - Get detailed file information

#### Collection Operations
- ✅ `get_collections()` - Get all collections
- ✅ `create_collection()` - Create new collection
- ✅ `delete_collection()` - Delete collection
- ✅ `add_file_to_collection()` - Add file to collection
- ✅ `remove_file_from_collection()` - Remove file from collection

#### Utility Methods
- ✅ `get_storage_info()` - Get storage usage data
- ✅ `can_edit_file()` - Check edit permissions
- ✅ `can_delete_file()` - Check delete permissions

## Usage Examples

### Initialize Controller
```python
from controller.document_controller import DocumentController

controller = DocumentController(
    username="admin",
    roles=["admin"],
    primary_role="admin",
    token="your-token-here"
)
```

### Get Files (Role-Based)
```python
# Admin sees all files
files = controller.get_files()

# With filters
files = controller.get_files(filters={
    'category': 'Syllabus',
    'extension': 'pdf',
    'search': 'chapter'
})
```

### Delete File (Soft Delete)
```python
success, message = controller.delete_file(
    filename="document.pdf",
    timestamp="2025-10-01 21:00:52"
)

if success:
    print(f"✅ {message}")
else:
    print(f"❌ {message}")
```

### Restore File
```python
success, message = controller.restore_file(
    filename="document.pdf",
    deleted_at="2025-10-01 22:00:00"
)
```

### Upload File
```python
success, message, file_data = controller.upload_file(
    source_path="C:/Users/Documents/file.pdf",
    custom_name="Important Document",
    category="Syllabus",
    description="Course syllabus for Fall 2025"
)

if success:
    print(f"✅ Uploaded: {file_data}")
```

### Create Collection
```python
success, message, collection_data = controller.create_collection(
    name="Fall 2025",
    icon="folder.png"
)
```

## Role-Based Access Control

### Admin
- ✅ See all files
- ✅ Delete any file
- ✅ Edit any file
- ✅ Create/delete collections

### Non-Admin (Student, Faculty, Staff)
- ✅ See only their own files
- ✅ Delete only their own files
- ✅ Edit only their own files
- ✅ View all collections (can be restricted later)

## Benefits of Controller Pattern

### 1. **Separation of Concerns**
- UI focuses on presentation
- Controller handles business logic
- Data layer handles persistence

### 2. **Reusability**
- Same controller works for all user dashboards
- No duplicate code across views

### 3. **Testability**
- Controller can be unit tested independently
- Mock data can be easily swapped

### 4. **Maintainability**
- Business logic changes in one place
- Easier to debug and extend

### 5. **Future-Proof**
- Easy to swap mock data with real API calls
- Just update controller methods, UI stays the same

## Next Steps

### When Backend is Ready:
1. Update controller methods to use API calls instead of JSON
2. Add authentication headers to requests
3. Handle async operations with loading states
4. Add caching for better performance

### Example Backend Integration:
```python
def get_files(self, filters=None):
    # Instead of: files = get_uploaded_files()
    
    response = requests.get(
        f"{API_URL}/api/documents/",
        headers={"Authorization": f"Bearer {self.token}"},
        params=filters
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        return []
```

## Files Modified

- ✅ `controller/__init__.py` - Package init
- ✅ `controller/document_controller.py` - Main controller (600+ lines)
- ✅ `Users/Admin/AdminDash.py` - Uses controller
- ✅ `Shared/deleted_files_view.py` - Uses controller + restore/delete
- ✅ `Shared/collection_view.py` - Uses controller

## Testing Checklist

- [ ] Upload file
- [ ] Delete file (soft delete)
- [ ] View deleted files
- [ ] Restore deleted file
- [ ] Permanently delete file
- [ ] Create collection
- [ ] Delete collection
- [ ] Add file to collection
- [ ] Remove file from collection
- [ ] Role-based file filtering
- [ ] Search functionality
- [ ] File details view

---

**Status:** ✅ Refactoring Complete - Ready for Testing!
