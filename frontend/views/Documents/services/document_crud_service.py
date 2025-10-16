"""
Document CRUD Service

Handles Create, Read, Update, Delete operations for documents and collections.
Manages data persistence to JSON files.
"""

import json
import os
from datetime import datetime



class DocumentCRUDService:
    """Service for managing document and collection data"""
    
    def __init__(self):
        """Initialize the CRUD service with paths to data files"""
        self.mock_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "Mock"
        )
        self.collections_file = os.path.join(self.mock_dir, "collections_data.json")
        self.files_file = os.path.join(self.mock_dir, "files_data.json")
    
    def _load_json(self, filepath):
        """Load JSON data from file with error handling"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # Handle empty file
                if not content:
                    print(f"Warning: Empty file '{filepath}', returning default structure")
                    return self._get_default_structure(filepath)
                data = json.loads(content)
                # Handle completely empty JSON objects
                if not data:
                    return self._get_default_structure(filepath)
                return data
        except FileNotFoundError:
            print(f"Warning: File not found '{filepath}', creating default structure")
            return self._get_default_structure(filepath)
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in '{filepath}': {e}, returning default structure")
            return self._get_default_structure(filepath)
    
    def _get_default_structure(self, filepath):
        """Get default structure based on file type"""
        if 'collections' in filepath:
            return {"collections": []}
        elif 'files' in filepath:
            return {"files": [], "next_file_id": 1}
        else:
            return {}
    
    def _save_json(self, filepath, data):
        """Save data to JSON file with error handling"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving JSON to '{filepath}': {e}")
            return False
    
    # ========== FILE ID MANAGEMENT ==========
    
    def _get_next_file_id(self):
        """
        Generate the next available file ID.
        
        Returns:
            int: Next available file ID
        """
        data = self._load_json(self.files_file)
        
        # Check if next_file_id exists in data
        if 'next_file_id' in data:
            next_id = data['next_file_id']
        else:
            # Initialize based on existing files
            all_files = data.get('files', [])
            
            # Find max existing file_id
            max_id = 0
            for file_data in all_files:
                if 'file_id' in file_data:
                    max_id = max(max_id, file_data['file_id'])
            
            next_id = max_id + 1
        
        # Increment and save
        data['next_file_id'] = next_id + 1
        self._save_json(self.files_file, data)
        
        print(f"Generated file_id: {next_id}")
        return next_id
    
    # ========== COLLECTION OPERATIONS ==========
    
    def create_collection(self, name, icon="folder.png", created_by="system", description=""):
        """
        Create a new collection.
        
        Args:
            name (str): Collection name
            icon (str): Icon filename
            
        Returns:
            dict: Result with success status and collection data
        """
        data = self._load_json(self.collections_file)
        collections = data.get("collections", [])
        
        # Generate new ID
        new_id = max([c.get("id", 0) for c in collections], default=0) + 1
        
        # Create new collection
        new_collection = {
            "id": new_id,
            "name": name,
            "icon": icon,
            "description": description,
            "files": [],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "created_by": created_by
        }
        
        collections.append(new_collection)
        data["collections"] = collections
        
        if self._save_json(self.collections_file, data):
            return {
                "success": True,
                "collection": new_collection
            }
        else:
            return {
                "success": False,
                "error": "Failed to save collection"
            }
    
    def get_all_collections(self):
        """Get all collections with safe fallback"""
        data = self._load_json(self.collections_file)
        collections = data.get("collections", [])
        # Ensure it's a list
        if not isinstance(collections, list):
            print(f"Warning: collections is not a list, returning empty list")
            return []
        return collections
    
    def get_collection_by_id(self, collection_id):
        """Get a collection by ID"""
        collections = self.get_all_collections()
        for collection in collections:
            if collection.get("id") == collection_id:
                return collection
        return None
    
    def get_collection_by_name(self, name):
        """Get a collection by name"""
        collections = self.get_all_collections()
        for collection in collections:
            if collection.get("name") == name:
                return collection
        return None
    
    # ========== FILE OPERATIONS ==========
    
    def add_file_to_collection(self, collection_id, filename, file_path, category, extension, uploader, role):
        """
        Add a file to a specific collection.
        
        Args:
            collection_id (int): ID of the collection
            filename (str): Name of the file
            file_path (str): Path to the file in storage
            category (str): File category
            extension (str): File extension
            uploader (str): Username of the uploader
            role (str): Role of the uploader (can include subroles with '-')
            
        Returns:
            dict: Result with success status
        """
        data = self._load_json(self.collections_file)
        collections = data.get("collections", [])
        
        # Generate unique file ID
        file_id = self._get_next_file_id()
        
        # Find the collection
        collection_found = False
        for collection in collections:
            if collection.get("id") == collection_id:
                collection_found = True
                
                # Add file to collection
                now = datetime.now()
                new_file = {
                    "file_id": file_id,  # NEW: Unique file identifier
                    "filename": filename,
                    "time": now.strftime("%I:%M %p").lower(),
                    "extension": extension,
                    "file_path": file_path,
                    "category": category,
                    "uploaded_date": now.strftime("%m/%d/%Y"),
                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "uploader": uploader,
                    "role": role,
                    "is_deleted": False,  # NEW: Track deletion status
                    "approval_status": "pending"  # NEW: pending, accepted, rejected
                }
                
                collection["files"].append(new_file)
                break
        
        if not collection_found:
            return {
                "success": False,
                "error": "Collection not found"
            }
        
        # Save updated collections
        data["collections"] = collections
        if self._save_json(self.collections_file, data):
            # Also add to files list (using the SAME file_id)
            self._add_to_files_list(filename, file_path, category, extension, uploader, role, file_id)
            
            # Add collection info to the file data
            new_file['collection_name'] = collection.get('name')
            new_file['collection_id'] = collection_id
            
            return {
                "success": True,
                "file": new_file
            }
        else:
            return {
                "success": False,
                "error": "Failed to save file"
            }
    
    def add_file_standalone(self, filename, file_path, category, extension, uploader, role):
        """
        Add a file to the files list (not in a collection).
        
        Args:
            filename (str): Name of the file
            file_path (str): Path to the file in storage
            category (str): File category
            extension (str): File extension
            uploader (str): Username of the uploader
            role (str): Role of the uploader (can include subroles with '-')
        """
        # Generate unique file ID
        file_id = self._get_next_file_id()
        
        now = datetime.now()
        new_file = {
            "file_id": file_id,  # NEW: Unique file identifier
            "filename": filename,
            "time": now.strftime("%I:%M %p").lower(),
            "extension": extension,
            "file_path": file_path,
            "category": category,
            "uploaded_date": now.strftime("%m/%d/%Y"),
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "uploader": uploader,
            "role": role,
            "is_deleted": False,  # NEW: Track deletion status
            "approval_status": "pending"  # NEW: pending, accepted, rejected
        }
        
        if self._add_to_files_list(filename, file_path, category, extension, uploader, role, file_id):
            return {
                "success": True,
                "file": new_file
            }
        else:
            return {
                "success": False,
                "error": "Failed to save file"
            }
    
    def _add_to_files_list(self, filename, file_path, category, extension, uploader, role, file_id=None):
        """Add a file to the files list with duplicate prevention"""
        data = self._load_json(self.files_file)
        all_files = data.get("files", [])
        
        # Generate file_id if not provided
        if file_id is None:
            file_id = self._get_next_file_id()
        
        # CRITICAL FIX: Check if file_id already exists (prevent duplicates)
        existing_file = next((f for f in all_files if f.get('file_id') == file_id), None)
        if existing_file:
            print(f"WARNING: File with file_id {file_id} already exists in files array. Skipping duplicate insertion.")
            return True  # Return success but don't add duplicate
        
        now = datetime.now()
        new_file = {
            "file_id": file_id,  # Unique file identifier
            "filename": filename,
            "time": now.strftime("%I:%M %p").lower(),
            "extension": extension,
            "file_path": file_path,
            "category": category,
            "uploaded_date": now.strftime("%m/%d/%Y"),
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "uploader": uploader,
            "role": role,
            "is_deleted": False,  # Track deletion status
            "approval_status": "pending"  # pending, accepted, rejected
        }
        
        all_files.append(new_file)
        data["files"] = all_files
        
        print(f"Added file to files array: file_id={file_id}, filename={filename}")
        return self._save_json(self.files_file, data)
    
    def get_all_uploaded_files(self):
        """Get all uploaded (non-deleted) files with safe fallback"""
        data = self._load_json(self.files_file)
        all_files = data.get("files", [])
        # Ensure it's a list
        if not isinstance(all_files, list):
            print(f"Warning: files is not a list, returning empty list")
            return []
        # Filter for non-deleted files
        uploaded_files = [f for f in all_files if not f.get('is_deleted', False)]
        return uploaded_files
    
    def get_files_by_collection(self, collection_id):
        """Get all files in a specific collection"""
        collection = self.get_collection_by_id(collection_id)
        if collection:
            return collection.get("files", [])
        return []
