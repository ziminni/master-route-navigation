# Mock data for Documents (current)

This folder contains local JSON data used by the Documents UI during development. The files are created/seeded by `initializer.py` and read via `data_loader.py`. These files are intended as development mock data and are not tracked in git.

## Files and schemas

- `files_data.json`

  Top-level keys:
  - `files`: array of file objects
  - `next_file_id`: integer counter

  File object fields (present in the current data):

  - `file_id` (int)
  - `filename` (string)
  - `time` (string) — human time like "05:22 pm"
  - `extension` (string)
  - `file_path` (string) — stored relative filename/path
  - `category` (string)
  - `collection` (string)
  - `uploaded_date` (string) — formatted date
  - `timestamp` (string) — ISO-like timestamp
  - `uploader` (string)
  - `role` (string)
  - `is_deleted` (bool)

  Example (from current data):

  ```json
  {
    "file_id": 1,
    "filename": "DICT Exam",
    "time": "05:22 pm",
    "extension": "pdf",
    "file_path": "DICT Exam_20251008_172231.pdf",
    "category": "None",
    "collection": "None",
    "uploaded_date": "10/08/2025",
    "timestamp": "2025-10-08 17:22:31",
    "uploader": "admin",
    "role": "admin",
    "is_deleted": false
  }
  ```

- `collections_data.json`

  Top-level keys:
  - `collections`: array of collection objects
  - `next_collection_id`: integer counter

  Collection object fields (current):
  - `id` (int)
  - `name` (string)
  - `icon` (string)
  - `description` (string)
  - `files` (array) — holds file objects or references
  - `created_at` (string)
  - `created_by` (string)

  Example (from current data):

  ```json
  {
    "id": 1,
    "name": "Syllabus",
    "icon": "folder1.png",
    "description": "Course syllabi and curriculum documents",
    "files": [],
    "created_at": "2025-10-08 17:22:06",
    "created_by": "system"
  }
  ```

- `storage_data.json`

  Current structure:

  ```json
  {
    "total_size_gb": 100.0,
    "used_size_gb": 0.0,
    "free_size_gb": 100.0,
    "usage_percentage": 0
  }
  ```

## Utilities (from `data_loader.py`)

Convenience functions used by the UI:

- `get_mock_data_path(filename)` — absolute path to a mock file
- `load_json_data(filename)` — safe load with sensible defaults when a file is missing, empty, or invalid
- `_get_default_structure(filename)` — returns default structures for files/collections/storage
- `get_uploaded_files()`, `get_deleted_files()`, `get_collections()`, `get_collection_by_name()`, `get_storage_data()` — reader helpers used throughout the front end

These functions are intentionally simple so they can be replaced by API calls later with minimal changes to the UI.

## Initializer (`initializer.py`)

On first run (or when files are missing) the initializer seeds default data:

- Default collections: Syllabus, Memo, Forms, Others
- `files_data.json` starts with an empty `files` array and `next_file_id` set to 1
- `storage_data.json` seeded with `total_size_gb` and zero usage

---
