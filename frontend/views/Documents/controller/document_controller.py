"""
Document Controller

Handles all business logic for document management operations.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from ..Mock.data_loader import (
    get_uploaded_files, 
    get_collections, 
    get_storage_data,
    get_deleted_files,
    get_collection_by_name,
    get_mock_data_path,
    load_json_data
)
from ..services.file_storage_service import FileStorageService


class DocumentController:
    """
    Controller for document management operations.
    
    This controller handles all business logic for:
    - File CRUD operations
    - Collection management
    - Role-based filtering
    - Soft delete/restore
    - File organization
    
    Args:
        username (str): Current user's username
        roles (list): List of user roles
        primary_role (str): User's primary role
        token (str): Authentication token
    """
    
    def __init__(self, username: str, roles: List[str], primary_role: str, token: str):
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.file_storage = FileStorageService()
        
    # ==================== FILE OPERATIONS ====================
    
    def get_files(self, include_deleted: bool = False, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Get files based on user role and filters.
        
        Args:
            include_deleted (bool): Whether to include deleted files
            filters (dict, optional): Filters to apply (category, uploader, etc.)
            
        Returns:
            list: List of file dictionaries
        """
        files = get_uploaded_files()
        
        # Filter based on role
        if self.primary_role.lower() != 'admin':
            # Non-admins only see their own files
            files = [f for f in files if f.get('uploader') == self.username]
        
        # Apply additional filters
        if filters:
            if 'category' in filters and filters['category']:
                files = [f for f in files if f.get('category') == filters['category']]
            if 'extension' in filters and filters['extension']:
                files = [f for f in files if f.get('extension') == filters['extension']]
            if 'search' in filters and filters['search']:
                search_term = filters['search'].lower()
                files = [f for f in files if search_term in f.get('filename', '').lower()]
        
        return files
    
    def get_deleted_files(self) -> List[Dict]:
        """
        Get deleted files (soft-deleted).
        
        Returns:
            list: List of deleted file dictionaries
        """
        deleted = get_deleted_files()
        
        # Filter based on role
        if self.primary_role.lower() != 'admin':
            deleted = [f for f in deleted if f.get('uploader') == self.username]
        
        return deleted
    
    def delete_file(self, file_id: int) -> Tuple[bool, str]:
        """
        Soft delete a file (mark as deleted with is_deleted=True and move to RecycleBin directory).
        
        Args:
            file_id (int): Unique file ID (REQUIRED)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            files_path = get_mock_data_path('files_data.json')
            with open(files_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            all_files = data.get('files', [])
            
            # Find the file to delete by file_id
            file_to_delete = None
            file_index = None
            for i, file_data in enumerate(all_files):
                # Skip already deleted files
                if file_data.get('is_deleted', False):
                    continue
                    
                if file_data.get('file_id') == file_id:
                    file_to_delete = file_data
                    file_index = i
                    break
            
            if file_to_delete and file_index is not None:
                # Get file_id for tracking
                deleted_file_id = file_to_delete.get('file_id')
                deleted_filename = file_to_delete.get('filename')
                
                # CRITICAL: Store which collections this file belongs to BEFORE removing
                collections_containing_file = self._get_collections_containing_file_by_id(deleted_file_id) if deleted_file_id else self._get_collections_containing_file(deleted_filename)
                if collections_containing_file:
                    file_to_delete['_original_collections'] = collections_containing_file
                    print(f"📋 Storing collection membership for file_id {deleted_file_id} ('{deleted_filename}'): {collections_containing_file}")
                
                # Move physical file to RecycleBin
                file_path = file_to_delete.get('file_path')
                if file_path:
                    result = self.file_storage.move_to_recycle_bin(file_path)
                    if result['success']:
                        file_to_delete['recycle_bin_path'] = result['recycle_bin_path']
                        file_to_delete['deleted_at'] = result['deleted_at']
                    else:
                        return False, f"Failed to move file to recycle bin: {result.get('error')}"
                else:
                    file_to_delete['deleted_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Mark as deleted and add deletion metadata
                file_to_delete['is_deleted'] = True
                file_to_delete['deleted_by'] = self.username
                
                # Update the file in place
                all_files[file_index] = file_to_delete
                data['files'] = all_files
                
                print(f"DEBUG delete_file: Saving to JSON. Total files in array: {len(all_files)}")
                print(f"DEBUG delete_file: File being saved - file_id={file_to_delete.get('file_id')}, is_deleted={file_to_delete.get('is_deleted')}, filename={file_to_delete.get('filename')}")
                
                with open(files_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                    
                print(f"DEBUG delete_file: Successfully saved to {files_path}")
                
                # CRITICAL FIX: Remove file from all collections (using file_id if available)
                if deleted_file_id:
                    success, msg, count = self.remove_file_from_all_collections_by_id(deleted_file_id)
                else:
                    success, msg, count = self.remove_file_from_all_collections(deleted_filename)
                    
                if success and count > 0:
                    print(f"✓ Removed file_id {deleted_file_id} ('{deleted_filename}') from {count} collection(s) during deletion")
                elif not success:
                    print(f"⚠ Warning: {msg}")
                
                return True, f"File '{deleted_filename}' (ID: {deleted_file_id}) moved to recycle bin"
            else:
                return False, f"File with ID {file_id} not found"
                
        except Exception as e:
            return False, f"Error deleting file: {str(e)}"
    
    def restore_file(self, file_id: int) -> Tuple[bool, str]:
        """
        Restore a soft-deleted file from RecycleBin (mark is_deleted=False).
        
        Args:
            file_id (int): Unique file ID (REQUIRED)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            files_path = get_mock_data_path('files_data.json')
            with open(files_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            all_files = data.get('files', [])
            
            # Find the file to restore by file_id
            file_to_restore = None
            file_index = None
            for i, file_data in enumerate(all_files):
                # Only look at deleted files
                if not file_data.get('is_deleted', False):
                    continue
                    
                if file_data.get('file_id') == file_id:
                    file_to_restore = file_data
                    file_index = i
                    break
            
            if file_to_restore and file_index is not None:
                # Get filename for logging
                restored_filename = file_to_restore.get('filename', 'Unknown')
                restored_file_id = file_to_restore.get('file_id')
                
                # Restore physical file from RecycleBin
                recycle_bin_path = file_to_restore.get('recycle_bin_path')
                original_path = file_to_restore.get('file_path')
                
                if recycle_bin_path and original_path:
                    result = self.file_storage.restore_from_recycle_bin(recycle_bin_path, original_path)
                    if not result['success']:
                        return False, f"Failed to restore file from recycle bin: {result.get('error')}"
                
                # Get original collections this file belonged to
                original_collections = file_to_restore.get('_original_collections', [])
                
                # Mark as not deleted and remove deletion metadata
                file_to_restore['is_deleted'] = False
                file_to_restore.pop('deleted_at', None)
                file_to_restore.pop('deleted_by', None)
                file_to_restore.pop('recycle_bin_path', None)
                file_to_restore.pop('_original_collections', None)  # Remove the tracking field
                
                # Update the file in place
                all_files[file_index] = file_to_restore
                data['files'] = all_files
                
                with open(files_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                # CRITICAL FIX: Restore file back to its original collections
                if original_collections:
                    restored_count = 0
                    for collection_id in original_collections:
                        collection_name = self._get_collection_name_by_id(collection_id)
                        success, msg = self.add_file_to_collection(collection_id, file_to_restore)
                        if success:
                            restored_count += 1
                            print(f"✓ Restored '{restored_filename}' (ID: {restored_file_id}) to collection '{collection_name}' (ID: {collection_id})")
                        else:
                            print(f"⚠ Warning: Could not restore to collection ID {collection_id}: {msg}")
                    
                    if restored_count > 0:
                        return True, f"File '{restored_filename}' (ID: {restored_file_id}) restored to {restored_count} collection(s)"
                
                return True, f"File '{restored_filename}' (ID: {restored_file_id}) restored successfully"
            else:
                return False, f"File with ID {file_id} not found in deleted files"
                
        except Exception as e:
            return False, f"Error restoring file: {str(e)}"
    
    def permanent_delete_file(self, file_id: int) -> Tuple[bool, str]:
        """
        Permanently delete a file (remove from files array and RecycleBin).
        
        Args:
            file_id (int): Unique file ID (REQUIRED)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            files_path = get_mock_data_path('files_data.json')
            with open(files_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            all_files = data.get('files', [])
            
            # Find the file to permanently delete by file_id
            file_to_delete = None
            file_index = None
            for i, file_data in enumerate(all_files):
                # Only look at deleted files
                if not file_data.get('is_deleted', False):
                    continue
                    
                if file_data.get('file_id') == file_id:
                    file_to_delete = file_data
                    file_index = i
                    break
            
            if file_to_delete and file_index is not None:
                # Get file info for logging
                deleted_file_id = file_to_delete.get('file_id')
                deleted_filename = file_to_delete.get('filename', 'Unknown')
                
                # Delete physical file from RecycleBin
                recycle_bin_path = file_to_delete.get('recycle_bin_path')
                if recycle_bin_path:
                    result = self.file_storage.permanent_delete_from_recycle_bin(recycle_bin_path)
                    if not result['success']:
                        print(f"Warning: Failed to delete from recycle bin: {result.get('error')}")
                
                # Remove from files array
                all_files.pop(file_index)
                data['files'] = all_files
                
                with open(files_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                # CRITICAL FIX: Also remove from collections by file_id
                success, msg, count = self.remove_file_from_all_collections_by_id(deleted_file_id)
                    
                if success and count > 0:
                    print(f"✓ Removed file_id {deleted_file_id} ('{deleted_filename}') from {count} collection(s) during permanent deletion")
                elif not success:
                    print(f"⚠ Warning: {msg}")
                
                return True, f"File '{deleted_filename}' (ID: {deleted_file_id}) permanently deleted"
            else:
                return False, f"File with ID {file_id} not found in deleted files"
                
        except Exception as e:
            return False, f"Error permanently deleting file: {str(e)}"
    
    def upload_file(self, source_path: str, custom_name: str = None, 
                   category: str = None, collection: str = None, description: str = None, 
                   force_override: bool = False) -> Tuple[bool, str, Optional[Dict]]:
        """
        Upload a new file with duplicate handling.
        
        Args:
            source_path (str): Path to the source file
            custom_name (str, optional): Custom name for the file
            category (str, optional): Category for the file
            collection (str, optional): Collection name the file belongs to
            description (str, optional): File description
            force_override (bool): If True, override existing file with same name
            
        Returns:
            tuple: (success: bool, message: str, file_data: dict or None)
        """
        try:
            # Determine the filename to use
            if custom_name:
                base_name = os.path.splitext(custom_name)[0]
            else:
                original_name = os.path.basename(source_path)
                base_name = os.path.splitext(original_name)[0]
            
            # Check for duplicate
            is_duplicate = self.file_storage.check_duplicate_filename(base_name)
            
            if is_duplicate:
                if force_override:
                    # Override: delete the old file entry
                    self._remove_file_entry(base_name)
                    final_name = base_name
                else:
                    # Auto-rename with (#)
                    final_name = self.file_storage.generate_unique_filename(base_name)
            else:
                final_name = base_name
            
            # Save file using storage service
            result = self.file_storage.save_file(source_path, final_name, category)
            
            if not result['success']:
                return False, result.get('error', 'Upload failed'), None
            
            # Add to JSON data first to get next_file_id
            files_path = get_mock_data_path('files_data.json')
            with open(files_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Generate unique file_id
            next_file_id = data.get('next_file_id', 1)
            file_id = next_file_id
            data['next_file_id'] = next_file_id + 1
            
            # Create file metadata with file_id
            file_data = {
                'file_id': file_id,  # CRITICAL: Unique file identifier
                'filename': result['filename'],
                'time': datetime.now().strftime("%I:%M %p").lower(),
                'extension': result['extension'],
                'file_path': result['file_path'],
                'category': category or 'None',
                'collection': collection or category or 'None',  # Add collection field with fallback
                'uploaded_date': datetime.now().strftime("%m/%d/%Y"),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'uploader': self.username,
                'role': self.primary_role,
                'is_deleted': False  # Track deletion status
            }
            
            if description:
                file_data['description'] = description
            
            # Add to files array (with duplicate prevention)
            all_files = data.get('files', [])
            
            # Check for duplicate file_id before appending
            existing_ids = [f.get('file_id') for f in all_files]
            if file_id not in existing_ids:
                all_files.append(file_data)
                data['files'] = all_files
            else:
                print(f"WARNING: Prevented duplicate file_id={file_id} from being added to files array")
                # Even if duplicate, we still return success since the file exists
                return True, "File already exists in the system", file_data
            
            print(f"DEBUG upload_file: Uploading file. file_id={file_id}, filename={file_data['filename']}, is_deleted={file_data['is_deleted']}")
            print(f"DEBUG upload_file: Total files in array after upload: {len(all_files)}")
            
            with open(files_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
            print(f"DEBUG upload_file: Successfully saved to {files_path}")
            
            success_msg = "File uploaded successfully"
            if is_duplicate and not force_override:
                success_msg += f" as '{final_name}'"
            elif is_duplicate and force_override:
                success_msg += " (previous version replaced)"
            
            return True, success_msg, file_data
            
        except Exception as e:
            return False, f"Error uploading file: {str(e)}", None
    
    def update_file(self, file_id: int, new_filename: str = None, 
                   category: str = None, description: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Update file metadata (filename, category, description).
        
        Args:
            file_id (int): Unique file ID (REQUIRED)
            new_filename (str, optional): New filename (if renaming)
            category (str, optional): New category
            description (str, optional): New description
            
        Returns:
            tuple: (success: bool, message: str, updated_file_data: dict or None)
        """
        try:
            files_path = get_mock_data_path('files_data.json')
            with open(files_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            all_files = data.get('files', [])
            
            # Find the file to update by file_id (only non-deleted files)
            file_to_update = None
            file_index = -1
            for i, file_data in enumerate(all_files):
                if file_data.get('is_deleted', False):
                    continue
                if file_data.get('file_id') == file_id:
                    file_to_update = file_data
                    file_index = i
                    break
            
            if file_to_update:
                old_filename = file_to_update.get('filename')
                
                # Update filename if provided and different
                if new_filename and new_filename != old_filename:
                    file_to_update['filename'] = new_filename
                    # Update extension if filename changed
                    file_to_update['extension'] = new_filename.split('.')[-1] if '.' in new_filename else file_to_update.get('extension', '')
                
                # Update category if provided
                if category is not None:
                    file_to_update['category'] = category if category != 'N/A' else None
                
                # Update description if provided
                if description is not None:
                    file_to_update['description'] = description
                
                # Save updated data
                all_files[file_index] = file_to_update
                data['files'] = all_files
                
                with open(files_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                # Also update in collections by file_id
                if new_filename and new_filename != old_filename:
                    self._update_file_in_collections_by_id(file_id, file_to_update)
                
                return True, f"File '{new_filename or old_filename}' (ID: {file_id}) updated successfully", file_to_update
            else:
                return False, f"File with ID {file_id} not found", None
                
        except Exception as e:
            return False, f"Error updating file: {str(e)}", None
    
    def _update_file_in_collections_by_id(self, file_id: int, updated_file_data: Dict) -> None:
        """
        Update file data in all collections that contain it (by file_id).
        
        Args:
            file_id (int): File ID to find
            updated_file_data (dict): New file data to replace with
        """
        try:
            collections_path = get_mock_data_path('collections_data.json')
            with open(collections_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            collections = data.get('collections', [])
            updated = False
            
            for collection in collections:
                files = collection.get('files', [])
                for i, file_data in enumerate(files):
                    if file_data.get('file_id') == file_id:
                        # Update the file data in this collection
                        collection['files'][i] = updated_file_data.copy()
                        updated = True
                        print(f"Updated file_id {file_id} in collection '{collection.get('name')}'")
            
            if updated:
                with open(collections_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error updating file in collections: {str(e)}")
    
    def _remove_file_entry(self, filename: str) -> bool:
        """
        Remove a file entry from JSON (used for override).
        
        Args:
            filename (str): Filename to remove
            
        Returns:
            bool: True if removed, False otherwise
        """
        try:
            files_path = get_mock_data_path('files_data.json')
            with open(files_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            all_files = data.get('files', [])
            # Remove file with matching filename (permanently)
            data['files'] = [f for f in all_files if f.get('filename') != filename]
            
            with open(files_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error removing file entry: {e}")
            return False
    
    # ==================== COLLECTION OPERATIONS ====================
    
    def get_collections(self) -> List[Dict]:
        """
        Get collections based on user role.
        
        Returns:
            list: List of collection dictionaries
        """
        collections = get_collections()
        
        # For now, all users see all collections
        # Can add role-based filtering later
        return collections
    
    def create_collection(self, name: str, icon: str = 'folder.png') -> Tuple[bool, str, Optional[Dict]]:
        """
        Create a new collection.
        
        Args:
            name (str): Collection name
            icon (str): Icon filename
            
        Returns:
            tuple: (success: bool, message: str, collection_data: dict or None)
        """
        try:
            collections_path = get_mock_data_path('collections_data.json')
            with open(collections_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            collections = data.get('collections', [])
            
            # Check if collection already exists
            if any(c['name'].lower() == name.lower() for c in collections):
                return False, f"Collection '{name}' already exists", None
            
            # Get next collection ID from counter (similar to file_id pattern)
            next_collection_id = data.get('next_collection_id', 1)
            collection_id = next_collection_id
            data['next_collection_id'] = next_collection_id + 1
            
            # Create new collection with unique collection_id
            collection_data = {
                'id': collection_id,  # Use the auto-incremented collection_id
                'name': name,
                'icon': icon,
                'files': [],
                'created_by': self.username,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            collections.append(collection_data)
            data['collections'] = collections
            
            with open(collections_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return True, f"Collection '{name}' created successfully (ID: {collection_id})", collection_data
            
        except Exception as e:
            return False, f"Error creating collection: {str(e)}", None
    
    def delete_collection(self, collection_id: int) -> Tuple[bool, str]:
        """
        Delete a collection if it's empty (contains no files).
        
        Args:
            collection_id (int): Unique collection ID (REQUIRED)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            collections_path = get_mock_data_path('collections_data.json')
            with open(collections_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            collections = data.get('collections', [])
            
            # Find the collection by ID and check if it's empty
            collection_found = False
            collection_index = -1
            collection_name = None
            file_count = 0
            
            for i, collection in enumerate(collections):
                if collection.get('id') == collection_id:
                    collection_found = True
                    collection_index = i
                    collection_name = collection.get('name')
                    file_count = len(collection.get('files', []))
                    break
            
            if not collection_found:
                return False, f"Collection with ID {collection_id} not found"
            
            # Check if collection is empty
            if file_count > 0:
                return False, (f"Cannot delete collection '{collection_name}' (ID: {collection_id}) because it contains {file_count} file(s). "
                             f"Please remove all files from this collection before deleting it.")
            
            # Collection is empty, proceed with deletion
            collections.pop(collection_index)
            
            # Save the updated collections data
            data['collections'] = collections
            
            with open(collections_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return True, f"Collection '{collection_name}' (ID: {collection_id}) deleted successfully"
                
        except Exception as e:
            return False, f"Error deleting collection: {str(e)}"
    
    def is_collection_empty(self, collection_id: int) -> Tuple[bool, int]:
        """
        Check if a collection is empty (contains no files).
        
        Args:
            collection_id (int): Unique collection ID (REQUIRED)
            
        Returns:
            tuple: (is_empty: bool, file_count: int)
                   Returns (False, -1) if collection not found
        """
        try:
            collections_path = get_mock_data_path('collections_data.json')
            with open(collections_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            collections = data.get('collections', [])
            
            for collection in collections:
                if collection.get('id') == collection_id:
                    file_count = len(collection.get('files', []))
                    return (file_count == 0, file_count)
            
            # Collection not found
            return False, -1
            
        except Exception as e:
            print(f"Error checking if collection is empty: {e}")
            return False, -1
    
    def add_file_to_collection(self, collection_id: int, file_data: Dict) -> Tuple[bool, str]:
        """
        Add a file to a collection.
        
        Args:
            collection_id (int): Unique collection ID (REQUIRED)
            file_data (dict): File data to add
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            collections_path = get_mock_data_path('collections_data.json')
            with open(collections_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            collections = data.get('collections', [])
            
            # Find the collection by ID
            for collection in collections:
                if collection.get('id') == collection_id:
                    collection_name = collection.get('name')
                    collection['files'].append(file_data)
                    
                    with open(collections_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    
                    return True, f"File added to collection '{collection_name}' (ID: {collection_id})"
            
            return False, f"Collection with ID {collection_id} not found"
            
        except Exception as e:
            return False, f"Error adding file to collection: {str(e)}"
    
    def remove_file_from_collection(self, collection_id: int, file_id: int) -> Tuple[bool, str]:
        """
        Remove a file from a collection.
        
        Args:
            collection_id (int): Unique collection ID (REQUIRED)
            file_id (int): Unique file ID (REQUIRED)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            collections_path = get_mock_data_path('collections_data.json')
            with open(collections_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            collections = data.get('collections', [])
            
            # Find the collection by ID
            for collection in collections:
                if collection.get('id') == collection_id:
                    collection_name = collection.get('name')
                    files = collection.get('files', [])
                    
                    # Remove the file by file_id
                    for i, file_data in enumerate(files):
                        if file_data.get('file_id') == file_id:
                            filename = file_data.get('filename')
                            files.pop(i)
                            
                            with open(collections_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=2)
                            
                            return True, f"File '{filename}' (ID: {file_id}) removed from collection '{collection_name}' (ID: {collection_id})"
                    
                    return False, f"File with ID {file_id} not found in collection '{collection_name}'"
            
            return False, f"Collection with ID {collection_id} not found"
            
        except Exception as e:
            return False, f"Error removing file from collection: {str(e)}"
    
    def _get_collections_containing_file(self, filename: str) -> List[str]:
        """
        Get list of collection names that contain a specific file.
        
        Args:
            filename (str): Name of the file to search for
            
        Returns:
            list: List of collection names containing this file
        """
        try:
            collections_path = get_mock_data_path('collections_data.json')
            with open(collections_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            collections = data.get('collections', [])
            collection_names = []
            
            for collection in collections:
                files = collection.get('files', [])
                for file_data in files:
                    if file_data.get('filename') == filename:
                        collection_names.append(collection.get('name'))
                        break
            
            return collection_names
        except Exception as e:
            print(f"Error getting collections containing file: {str(e)}")
            return []
    
    def remove_file_from_all_collections(self, filename: str) -> Tuple[bool, str, int]:
        """
        Remove a file from ALL collections (used when file is deleted).
        
        Args:
            filename (str): Name of the file to remove from all collections
            
        Returns:
            tuple: (success: bool, message: str, count: int) - count is number of collections affected
        """
        try:
            collections_path = get_mock_data_path('collections_data.json')
            with open(collections_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            collections = data.get('collections', [])
            collections_affected = 0
            
            # Search through all collections and remove the file
            for collection in collections:
                files = collection.get('files', [])
                original_count = len(files)
                
                # Remove all instances of this filename from the collection
                collection['files'] = [f for f in files if f.get('filename') != filename]
                
                # Track if this collection was affected
                if len(collection['files']) < original_count:
                    collections_affected += 1
                    print(f"Removed '{filename}' from collection '{collection.get('name')}'")
            
            # Save updated collections data
            if collections_affected > 0:
                with open(collections_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                return True, f"File removed from {collections_affected} collection(s)", collections_affected
            else:
                return True, "File was not in any collections", 0
            
        except Exception as e:
            return False, f"Error removing file from collections: {str(e)}", 0
    
    def _get_collections_containing_file_by_id(self, file_id: int) -> List[int]:
        """
        Get list of collection IDs that contain a specific file by ID.
        
        Args:
            file_id (int): Unique ID of the file to search for
            
        Returns:
            list: List of collection IDs containing this file
        """
        try:
            collections_path = get_mock_data_path('collections_data.json')
            with open(collections_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            collections = data.get('collections', [])
            collection_ids = []
            
            for collection in collections:
                files = collection.get('files', [])
                for file_data in files:
                    if file_data.get('file_id') == file_id:
                        collection_ids.append(collection.get('id'))
                        break
            
            return collection_ids
        except Exception as e:
            print(f"Error getting collections containing file_id {file_id}: {str(e)}")
            return []
    
    def remove_file_from_all_collections_by_id(self, file_id: int) -> Tuple[bool, str, int]:
        """
        Remove a file from ALL collections by file_id (used when file is deleted).
        
        Args:
            file_id (int): Unique ID of the file to remove from all collections
            
        Returns:
            tuple: (success: bool, message: str, count: int) - count is number of collections affected
        """
        try:
            collections_path = get_mock_data_path('collections_data.json')
            with open(collections_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            collections = data.get('collections', [])
            collections_affected = 0
            
            # Search through all collections and remove the file
            for collection in collections:
                files = collection.get('files', [])
                original_count = len(files)
                
                # Remove all instances of this file_id from the collection
                collection['files'] = [f for f in files if f.get('file_id') != file_id]
                
                # Track if this collection was affected
                if len(collection['files']) < original_count:
                    collections_affected += 1
                    print(f"Removed file_id {file_id} from collection '{collection.get('name')}'")
            
            # Save updated collections data
            if collections_affected > 0:
                with open(collections_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                return True, f"File removed from {collections_affected} collection(s)", collections_affected
            else:
                return True, "File was not in any collections", 0
            
        except Exception as e:
            return False, f"Error removing file from collections: {str(e)}", 0
    
    # ==================== COLLECTION HELPER METHODS ====================
    
    def _get_collection_by_id(self, collection_id: int) -> Optional[Dict]:
        """
        Get full collection data by ID.
        
        Args:
            collection_id (int): Collection ID
            
        Returns:
            dict: Collection data or None if not found
        """
        try:
            collections_path = get_mock_data_path('collections_data.json')
            with open(collections_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            collections = data.get('collections', [])
            for collection in collections:
                if collection.get('id') == collection_id:
                    return collection
            return None
        except Exception as e:
            print(f"Error getting collection by ID {collection_id}: {str(e)}")
            return None
    
    def _get_collection_name_by_id(self, collection_id: int) -> Optional[str]:
        """
        Get collection name from ID.
        
        Args:
            collection_id (int): Collection ID
            
        Returns:
            str: Collection name or None if not found
        """
        collection = self._get_collection_by_id(collection_id)
        return collection.get('name') if collection else None
    
    # ==================== UTILITY METHODS ====================
    
    def get_file_details(self, file_id: int) -> Optional[Dict]:
        """
        Get detailed information about a file by its ID.
        
        Args:
            file_id (int): Unique file ID (REQUIRED)
            
        Returns:
            dict or None: File details if found
        """
        files = get_uploaded_files()
        
        for file_data in files:
            if file_data.get('file_id') == file_id:
                return file_data
        
        return None
    
    def get_storage_info(self) -> Dict:
        """
        Get storage usage information.
        
        Returns:
            dict: Storage information
        """
        return get_storage_data()
    
    def cleanup_old_recycle_bin_files(self, days: int = 15) -> Tuple[bool, str, int]:
        """
        Automatically cleanup files from RecycleBin older than specified days.
        Also removes them from deleted_files in JSON.
        
        Args:
            days (int): Number of days after which files should be deleted (default: 15)
            
        Returns:
            tuple: (success: bool, message: str, count: int)
        """
        try:
            # Cleanup physical files from RecycleBin
            result = self.file_storage.cleanup_old_recycle_bin_files(days)
            
            if not result['success']:
                return False, result.get('error', 'Cleanup failed'), 0
            
            deleted_filenames = result.get('deleted_files', [])
            deleted_count = result.get('deleted_count', 0)
            
            if deleted_count > 0:
                # Remove entries from files array in JSON (permanently delete)
                files_path = get_mock_data_path('files_data.json')
                with open(files_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                all_files = data.get('files', [])
                
                # Filter out files that were auto-deleted
                updated_files = []
                for file_data in all_files:
                    recycle_bin_path = file_data.get('recycle_bin_path')
                    if recycle_bin_path not in deleted_filenames:
                        updated_files.append(file_data)
                
                data['files'] = updated_files
                
                with open(files_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                return True, f"Automatically cleaned up {deleted_count} old file(s) from recycle bin", deleted_count
            else:
                return True, "No old files to cleanup", 0
                
        except Exception as e:
            return False, f"Error during cleanup: {str(e)}", 0
    
    def get_recycle_bin_file_info(self, filename: str, deleted_at: str = None) -> Optional[Dict]:
        """
        Get information about a file in the recycle bin including its age.
        
        Args:
            filename (str): Name of the file
            deleted_at (str, optional): Deletion timestamp
            
        Returns:
            dict or None: File info with age_days, days_remaining
        """
        try:
            deleted_files = self.get_deleted_files()
            
            for file_data in deleted_files:
                if file_data['filename'] == filename:
                    if deleted_at is None or file_data.get('deleted_at') == deleted_at:
                        recycle_bin_path = file_data.get('recycle_bin_path')
                        if recycle_bin_path:
                            age_days = self.file_storage.get_recycle_bin_file_age(recycle_bin_path)
                            if age_days is not None:
                                file_data['age_days'] = age_days
                                file_data['days_remaining'] = max(0, 15 - age_days)
                        return file_data
            
            return None
        except Exception as e:
            print(f"Error getting recycle bin file info: {str(e)}")
            return None
    
    def can_edit_file(self, file_data: Dict) -> bool:
        """
        Check if current user can edit a file.
        
        Args:
            file_data (dict): File data to check
            
        Returns:
            bool: True if user can edit
        """
        if self.primary_role.lower() == 'admin':
            return True
        
        return file_data.get('uploader') == self.username
    
    def can_delete_file(self, file_data: Dict) -> bool:
        """
        Check if current user can delete a file.
        
        Args:
            file_data (dict): File data to check
            
        Returns:
            bool: True if user can delete
        """
        if self.primary_role.lower() == 'admin':
            return True
        
        return file_data.get('uploader') == self.username
    
    def update_file_collection(self, filename: str, collection_name: str = None, timestamp: str = None) -> Tuple[bool, str]:
        """
        Update the collection field for a specific file.
        
        Args:
            filename (str): Name of the file
            collection_name (str, optional): New collection name (None to remove from collection)
            timestamp (str, optional): File timestamp for identification
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            files_path = get_mock_data_path('files_data.json')
            with open(files_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            uploaded_files = data.get('uploaded_files', [])
            file_found = False
            
            for file_data in uploaded_files:
                if file_data['filename'] == filename:
                    if timestamp is None or file_data.get('timestamp') == timestamp:
                        file_data['collection'] = collection_name or 'None'
                        file_found = True
                        break
            
            if file_found:
                data['uploaded_files'] = uploaded_files
                
                with open(files_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                return True, f"File collection updated successfully"
            else:
                return False, f"File '{filename}' not found"
                
        except Exception as e:
            return False, f"Error updating file collection: {str(e)}"
