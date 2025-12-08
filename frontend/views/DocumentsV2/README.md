# DocumentsV2 - CISC Virtual Hub Document Management

A modern, Google Drive-inspired document management interface built with PyQt6 and Django REST Framework.

## 🎯 Overview

DocumentsV2 provides a complete document management solution with:
- **File browsing** with list view
- **Folder hierarchy** with breadcrumb navigation
- **Upload management** with progress tracking
- **Search & filtering** by category, name, date, size
- **Context menus** for quick actions
- **Trash bin** with restore functionality
- **Role-based access control**

## 📁 Project Structure

```
DocumentsV2/
├── __init__.py                 # Package initialization
├── main_window.py             # Main application window
├── ICONS_NEEDED.md            # Icon requirements documentation
├── README.md                  # This file
│
├── widgets/                   # Reusable UI components
│   ├── __init__.py
│   ├── sidebar.py            # Left navigation panel
│   ├── toolbar.py            # Top action bar
│   ├── breadcrumb.py         # Folder navigation breadcrumbs
│   └── file_list.py          # Document table view
│
├── dialogs/                   # Dialog windows
│   ├── __init__.py
│   ├── upload_dialog.py      # File upload interface
│   └── folder_dialog.py      # New folder creation
│
└── services/                  # Backend API communication
    ├── __init__.py
    └── document_service.py   # Django REST API client
```

## 🚀 Features Implemented (Priority 1)

### ✅ Sidebar Navigation
- **My Drive**: All accessible documents
- **Recent**: Recently accessed files (via activity log)
- **Starred**: Featured documents
- **Trash**: Soft-deleted items with restore
- **Categories**: Hierarchical category browsing
- **Storage Indicator**: Visual storage quota display

### ✅ Toolbar
- **Upload Button**: Opens file upload dialog
- **New Folder**: Creates folders with category/parent selection
- **Refresh**: Reloads current view
- **Search Bar**: Full-text document search
- **Sort Dropdown**: Name, Date, Size (ascending/descending)

### ✅ Breadcrumb Navigation
- Shows current folder path
- Clickable segments for quick navigation
- Auto-updates when navigating folders

### ✅ File List View
- Sortable table with columns: Name, Owner, Modified, Size
- Checkboxes for multi-selection
- File type icons (emoji placeholders)
- Double-click to open folders or download files
- Right-click context menu with actions

### ✅ Context Menu Actions
**For Documents:**
- Open (download)
- Download
- Move to... (placeholder)
- Rename (placeholder)
- Details
- Move to Trash

**For Folders:**
- Open (navigate into)
- Rename (placeholder)
- Delete

**For Trash Items:**
- Restore
- Delete Permanently (placeholder)

### ✅ Upload Dialog
- Multiple file selection
- Category selection (required)
- Folder selection (optional)
- Progress bars for each file
- Upload status tracking

### ✅ Folder Creation
- Folder name input
- Category selection (required)
- Parent folder selection (optional)
- Description field (optional)

## 🔌 Backend Integration

### API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /api/documents/documents/` | List all documents |
| `GET /api/documents/documents/my-recent/` | Get recent documents |
| `GET /api/documents/documents/trash/` | Get deleted documents |
| `GET /api/documents/documents/{id}/` | Get document details |
| `POST /api/documents/documents/` | Upload new document |
| `DELETE /api/documents/documents/{id}/` | Soft delete document |
| `POST /api/documents/documents/{id}/restore/` | Restore from trash |
| `POST /api/documents/documents/{id}/move/` | Move to folder |
| `GET /api/documents/documents/{id}/download/` | Get download URL |
| `GET /api/documents/folders/` | List folders |
| `POST /api/documents/folders/` | Create folder |
| `GET /api/documents/folders/{id}/breadcrumbs/` | Get folder path |
| `GET /api/documents/categories/` | List categories |

### DocumentService Methods

```python
# Documents
get_documents(filters)       # List with optional filters
get_my_recent()             # Recent documents
get_trash()                 # Deleted documents
get_document(doc_id)        # Document details
upload_document(...)        # Upload new file
move_document(doc_id, ...)  # Move to folder
restore_document(doc_id)    # Restore from trash
delete_document(doc_id)     # Soft delete
download_document(doc_id)   # Get download URL

# Folders
get_folders(parent_id)      # List folders
create_folder(...)          # Create new folder
get_folder_breadcrumbs(...)# Get folder path

# Categories
get_categories()            # List all categories

# Approvals (Faculty/Admin)
get_pending_approvals()     # Pending approvals
approve_document(...)       # Approve document
reject_document(...)        # Reject document
```

## 📖 Usage Example

### Basic Integration

```python
from PyQt6.QtWidgets import QApplication
from frontend.views.DocumentsV2 import DocumentsV2MainWindow
import sys

# Create application
app = QApplication(sys.argv)

# Create main window with user session
window = DocumentsV2MainWindow(
    username="john.doe",
    roles=["student"],
    primary_role="student",
    token="your_jwt_token_here"
)

# Show window
window.show()

# Run application
sys.exit(app.exec())
```

### Integration with Router

```python
# In your router's _build_page_classes method
from frontend.views.DocumentsV2 import DocumentsV2MainWindow

# Add to page classes
page_classes['main_10'] = DocumentsV2MainWindow  # ID 10 for Documents
```

## 🎨 UI Design Notes

### Current State (Emoji Icons)
All icons are currently emoji placeholders:
- 📄 PDF files
- 📁 Folders
- ⬆️ Upload
- 🗑️ Trash
- etc.

### Production Icons
See `ICONS_NEEDED.md` for:
- Required icon list
- Recommended icon packs
- Size specifications
- Color guidelines
- File naming conventions

### Styling
Currently minimal styling for rapid development. Future enhancements:
- Custom color scheme matching CISC branding
- Hover effects on list items
- Selected item highlighting
- Loading animations
- Toast notifications

## 🔐 Role-Based Access Control

| Feature | Student | Staff | Faculty | Admin |
|---------|---------|-------|---------|-------|
| View approved docs | ✅ | ✅ | ✅ | ✅ |
| Upload docs | ❌ | ⚠️ (needs approval) | ✅ | ✅ |
| Create folders | ❌ | ❌ | ✅ | ✅ |
| Delete own docs | ❌ | ✅ | ✅ | ✅ |
| Delete any docs | ❌ | ❌ | ❌ | ✅ |
| View all trash | ❌ | ❌ | ❌ | ✅ |

## 🐛 Known Limitations / TODOs

### Not Yet Implemented
1. **Drag & Drop Upload** - Deliberately excluded per requirements
2. **Grid View** - Deliberately excluded per requirements
3. **PDF Preview** - Deliberately excluded per requirements
4. **Details Panel** - Deliberately excluded per requirements
5. **Move Dialog** - Shows placeholder message
6. **Rename Functionality** - Shows placeholder message
7. **Permanent Delete** - Shows placeholder message
8. **User Favorites** - Requires new backend model
9. **Download Implementation** - Currently shows URL instead of downloading
10. **Actual Progress Tracking** - Upload progress is simulated

### Future Enhancements (Priority 2)
- Approval workflow panel for faculty/admin
- Bulk actions on selected items
- Advanced filter panel
- Activity timeline view
- Storage quota enforcement
- File preview (PDF, images)
- Share with specific users
- Version history view
- Duplicate file detection

## 🧪 Testing Checklist

### Manual Testing Steps

1. **Startup**
   - [ ] Window opens without errors
   - [ ] Categories load in sidebar
   - [ ] Documents load in main view
   - [ ] Storage indicator displays

2. **Navigation**
   - [ ] Click "My Drive" - shows all documents
   - [ ] Click "Recent" - shows recent documents
   - [ ] Click "Starred" - shows featured documents
   - [ ] Click "Trash" - shows deleted documents
   - [ ] Click category - filters by category

3. **File Operations**
   - [ ] Double-click document - downloads
   - [ ] Double-click folder - navigates into folder
   - [ ] Right-click document - shows context menu
   - [ ] Context menu actions work correctly

4. **Upload**
   - [ ] Click "Upload" button - opens dialog
   - [ ] Select files - displays in list
   - [ ] Select category - enables upload button
   - [ ] Click "Upload All" - uploads files
   - [ ] Success message displays
   - [ ] Documents appear in list

5. **Folder Creation**
   - [ ] Click "New Folder" - opens dialog
   - [ ] Enter name and category - enables create button
   - [ ] Click "Create" - creates folder
   - [ ] Folder appears in list

6. **Search & Sort**
   - [ ] Enter search text - filters documents
   - [ ] Change sort option - reorders list
   - [ ] Clear search - shows all documents

7. **Trash Operations**
   - [ ] Delete document - moves to trash
   - [ ] Navigate to trash - document appears
   - [ ] Right-click in trash - shows restore option
   - [ ] Restore document - moves back to original location

## 🔧 Configuration

### Backend URL
Default: `http://localhost:8000`

To change:
```python
service = DocumentService(
    base_url="http://your-backend-url:port",
    token="your_token"
)
```

### File Upload Limits
Controlled by backend `DocumentType.max_file_size_mb`

### Storage Quota
Currently calculated from user's uploaded documents. To implement quotas:
1. Add `storage_quota_gb` field to User model
2. Calculate used space from document file sizes
3. Update sidebar storage indicator

## 📚 Code Documentation

All classes and methods include docstrings with:
- Purpose description
- Parameter explanations
- Return value descriptions
- Usage examples where applicable

### Key Classes

**MainWindow** (`main_window.py`)
- Main application coordinator
- Handles all user interactions
- Manages API calls and data flow

**Sidebar** (`widgets/sidebar.py`)
- Navigation panel
- Category display
- Storage indicator

**Toolbar** (`widgets/toolbar.py`)
- Action buttons
- Search bar
- Sort dropdown

**FileListView** (`widgets/file_list.py`)
- Document table display
- Multi-selection support
- Context menu handling

**DocumentService** (`services/document_service.py`)
- API communication layer
- Request/response handling
- Error management

## 🤝 Contributing

When adding features:
1. Follow existing code structure
2. Add comprehensive docstrings
3. Handle errors gracefully
4. Test with different user roles
5. Update this README

## 📄 License

Part of CISC Virtual Hub project - ITSD81 Desktop Application Development
Central Mindanao University
