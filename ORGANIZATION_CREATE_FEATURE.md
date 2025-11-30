# Organization Create Feature - Admin Role

This document describes the implementation of the create organization feature for admin users.

## Overview

The create organization feature has been implemented with a REST API backend and PyQt frontend integration. When an admin creates an organization, the data is now stored in the database via API calls instead of just JSON files.

## Implementation Details

### Backend (Django REST Framework)

1. **Serializer** (`backend/apps/Organizations/serializers.py`)
   - `OrganizationSerializer`: Handles serialization/deserialization of Organization model
   - Validates organization name is not empty
   - Validates org_level is either 'col' or 'prog'
   - Handles main_org as a many-to-many relationship (list of organization IDs)
   - Fields: id, name, description, status, logo_path, created_at, org_level, main_org

2. **View** (`backend/apps/Organizations/views.py`)
   - `OrganizationListView`: APIView for listing all organizations
     - GET endpoint that retrieves all organizations from database
     - Returns organizations ordered by creation date (newest first)
   - `OrganizationCreateView`: APIView for creating organizations
     - POST endpoint that accepts organization data
     - Handles main_org as list of IDs (supports comma-separated strings or arrays)
     - Returns success/error response with created organization data

3. **URLs** (`backend/apps/Organizations/urls.py` and `backend/config/urls.py`)
   - Endpoint: `GET /api/organizations/` - List all organizations
   - Endpoint: `POST /api/organizations/create/` - Create organization
   - Integrated into main URL configuration

### Frontend (PyQt6)

1. **API Service** (`frontend/services/organization_api_service.py`)
   - `OrganizationAPIService`: Handles all API calls to the backend
   - `fetch_organizations()`: Fetches all organizations from database via GET request
   - `create_organization()`: Sends POST request to create organization
   - Accepts org_level and main_org_ids parameters
   - Handles file uploads for logos
   - Provides error handling for connection issues

2. **Dialog Update** (`frontend/widgets/orgs_custom_widgets/dialogs.py`)
   - `CreateOrgDialog.confirm()`: Updated to use API service
   - Replaced "Brief Overview" field with "Organization Level" dropdown (College/Program)
   - Added "Main Organization(s)" multi-select list widget
   - **Main Org list now fetches from database via API** instead of JSON file
   - Calls API to create organization in database
   - Still maintains local JSON for backwards compatibility
   - Shows success/error messages to user

3. **Organization Display** (`frontend/views/Organizations/BrowseView/Base/faculty_admin_base.py`)
   - `load_orgs()`: **Now fetches organizations from database via API**
   - Falls back to JSON data if API is unavailable
   - Displays organizations from database in the UI

## How to Test

### 1. Start the Backend Server

```cmd
cd backend
python manage.py runserver
```

The server will start at `http://localhost:8000`

### 2. Run Database Migrations (if not already done)

```cmd
cd backend
python manage.py makemigrations Organizations
python manage.py migrate
```

### 3. Start the Frontend Application

```cmd
python launch.py
```

### 4. Test Creating an Organization

1. Log in as an admin user (the application should redirect you to the admin page)
2. Click the "+ Create Organization/Branch" button (bottom right)
3. Select "Organization" from the dialog
4. Fill in the organization details:
   - Name (required)
   - Organization Level: Choose between "College" or "Program"
   - Main Organization(s): Select parent organizations (optional, can select multiple)
   - Description
   - Upload a logo (optional)
5. Click "Confirm"

### 5. Verify the Creation

- Check that a success message appears
- Check that the organization appears in the list
- Check the backend database:
  ```cmd
  cd backend
  python manage.py shell
  ```
  ```python
  from apps.Organizations.models import Organization
  Organization.objects.all()
  ```

## API Endpoint Details

### List Organizations

**Endpoint:** `GET /api/organizations/`

**Success Response (200 OK):**
```json
{
    "message": "Organizations retrieved successfully",
    "data": [
        {
            "id": 1,
            "name": "Organization Name",
            "description": "Organization description",
            "status": "active",
            "logo_path": "/path/to/logo",
            "created_at": "2025-11-30T12:00:00Z",
            "org_level": "col",
            "main_org": [1, 2]
        }
    ],
    "count": 1
}
```

### Create Organization

**Endpoint:** `POST /api/organizations/create/`

**Request Body:**
```json
{
    "name": "Organization Name",
    "description": "Organization description",
    "org_level": "col",  // "col" for college-level, "prog" for program-level
    "status": "active",
    "main_org": [1, 2],  // Array of parent organization IDs (optional)
    "logo_path": <file upload (optional)>
}
```

**Success Response (201 Created):**
```json
{
    "message": "Organization created successfully",
    "data": {
        "id": 1,
        "name": "Organization Name",
        "description": "Organization description",
        "status": "active",
        "logo_path": "/path/to/logo",
        "created_at": "2025-11-30T12:00:00Z",
        "org_level": "col",
        "main_org": [1, 2]
    }
}
```

**Error Response (400 Bad Request):**
```json
{
    "message": "Failed to create organization",
    "errors": {
        "name": ["This field is required."]
    }
}
```

## Configuration Notes

### Security Settings (Simplified for Development)

The following security features have been disabled for simple testing:
- Authentication: `AllowAny` permission class
- CSRF protection: Disabled
- CORS: Allowed for all origins

**⚠️ IMPORTANT:** These settings are for development only. Before deploying to production:
1. Enable authentication
2. Enable CSRF protection
3. Configure proper CORS settings
4. Add proper permission classes

## Data Storage

Currently, the system maintains dual storage:
1. **Database (Primary)**: Organizations are stored in the SQLite database via the Django ORM
2. **JSON File (Backwards Compatibility)**: Organizations are also saved to the local JSON file

This approach allows gradual migration while maintaining compatibility with existing code.

## Future Improvements

1. Remove JSON file dependency entirely
2. Add authentication and authorization
3. Add validation for duplicate organization names
4. Implement file size limits for logo uploads
5. Add organization listing endpoint
6. Add organization update and delete endpoints
7. Handle branches properly with foreign key relationships
