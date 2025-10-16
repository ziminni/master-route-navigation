"""
File Storage Service

Handles physical file operations for the document management system.
Copies uploaded files to the FileStorage directory and manages file paths.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path


class FileStorageService:
    """Service for managing file storage operations"""
    
    def __init__(self, storage_directory=None):
        """
        Initialize the file storage service.
        
        Args:
            storage_directory (str): Path to storage directory. 
                                    Defaults to FileStorage in Documents folder.
        """
        if storage_directory is None:
            # Get the Documents folder path
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            storage_directory = os.path.join(current_dir, "FileStorage")
        
        self.storage_directory = storage_directory
        self.recycle_bin_directory = os.path.join(storage_directory, "RecycleBin")
        self._ensure_storage_directory_exists()
        self._ensure_recycle_bin_exists()
    
    def _ensure_storage_directory_exists(self):
        """Create storage directory if it doesn't exist"""
        os.makedirs(self.storage_directory, exist_ok=True)
    
    def _ensure_recycle_bin_exists(self):
        """Create RecycleBin directory if it doesn't exist"""
        os.makedirs(self.recycle_bin_directory, exist_ok=True)
    
    def save_file(self, source_path, custom_name=None, category=None):
        """
        Copy a file to the storage directory with a unique name.
        
        Args:
            source_path (str): Path to the source file
            custom_name (str, optional): Custom name for the file
            category (str, optional): Category for organizing files
            
        Returns:
            dict: File information with keys:
                - success (bool): Whether the operation succeeded
                - file_path (str): Relative path in storage
                - filename (str): Name of the stored file
                - extension (str): File extension
                - error (str, optional): Error message if failed
        """
        try:
            # Validate source file exists
            if not os.path.exists(source_path):
                return {
                    "success": False,
                    "error": f"Source file not found: {source_path}"
                }
            
            # Get original filename and extension
            original_name = os.path.basename(source_path)
            name_without_ext, extension = os.path.splitext(original_name)
            
            # Use custom name if provided, otherwise use original
            if custom_name:
                # Remove extension from custom name if present
                custom_name_clean = os.path.splitext(custom_name)[0]
                base_name = custom_name_clean
            else:
                base_name = name_without_ext
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_name = f"{base_name}_{timestamp}{extension}"
            
            # Create category subdirectory if specified
            if category and category.lower() != "none":
                dest_directory = os.path.join(self.storage_directory, category)
                os.makedirs(dest_directory, exist_ok=True)
                dest_path = os.path.join(dest_directory, unique_name)
                relative_path = os.path.join(category, unique_name)
            else:
                dest_path = os.path.join(self.storage_directory, unique_name)
                relative_path = unique_name
            
            # Copy the file
            shutil.copy2(source_path, dest_path)
            
            return {
                "success": True,
                "file_path": relative_path,
                "filename": base_name,
                "extension": extension.lstrip('.'),
                "full_path": dest_path
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save file: {str(e)}"
            }
    
    def get_file_path(self, relative_path):
        """
        Get the full path to a stored file.
        
        Args:
            relative_path (str): Relative path in storage
            
        Returns:
            str: Full path to the file
        """
        return os.path.join(self.storage_directory, relative_path)
    
    def move_to_recycle_bin(self, relative_path):
        """
        Move a file to the RecycleBin directory (soft delete).
        
        Args:
            relative_path (str): Relative path in storage
            
        Returns:
            dict: Result with success status, recycle_bin_path, and optional error message
        """
        try:
            full_path = self.get_file_path(relative_path)
            if not os.path.exists(full_path):
                return {
                    "success": False,
                    "error": "File not found"
                }
            
            # Generate unique name in recycle bin with deletion timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(relative_path)
            name_without_ext, extension = os.path.splitext(filename)
            recycle_filename = f"{name_without_ext}_deleted_{timestamp}{extension}"
            recycle_bin_path = os.path.join(self.recycle_bin_directory, recycle_filename)
            
            # Move file to recycle bin
            shutil.move(full_path, recycle_bin_path)
            
            # CRITICAL FIX: Update the file's modification time to NOW
            # This ensures auto-cleanup calculates age from deletion time, not original file creation time
            import time
            current_time = time.time()
            os.utime(recycle_bin_path, (current_time, current_time))
            
            return {
                "success": True,
                "recycle_bin_path": recycle_filename,
                "deleted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to move file to recycle bin: {str(e)}"
            }
    
    def restore_from_recycle_bin(self, recycle_filename, original_relative_path):
        """
        Restore a file from the RecycleBin directory.
        
        Args:
            recycle_filename (str): Filename in recycle bin
            original_relative_path (str): Original relative path to restore to
            
        Returns:
            dict: Result with success status and optional error message
        """
        try:
            recycle_path = os.path.join(self.recycle_bin_directory, recycle_filename)
            if not os.path.exists(recycle_path):
                return {
                    "success": False,
                    "error": "File not found in recycle bin"
                }
            
            # Restore to original location
            restore_path = self.get_file_path(original_relative_path)
            
            # Ensure target directory exists
            os.makedirs(os.path.dirname(restore_path), exist_ok=True)
            
            # Move file back from recycle bin
            shutil.move(recycle_path, restore_path)
            
            return {"success": True}
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to restore file: {str(e)}"
            }
    
    def permanent_delete_from_recycle_bin(self, recycle_filename):
        """
        Permanently delete a file from the RecycleBin directory.
        
        Args:
            recycle_filename (str): Filename in recycle bin
            
        Returns:
            dict: Result with success status and optional error message
        """
        try:
            recycle_path = os.path.join(self.recycle_bin_directory, recycle_filename)
            if os.path.exists(recycle_path):
                os.remove(recycle_path)
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": "File not found in recycle bin"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to permanently delete file: {str(e)}"
            }
    
    def cleanup_old_recycle_bin_files(self, days=15):
        """
        Automatically delete files from RecycleBin older than specified days.
        
        Args:
            days (int): Number of days after which files should be deleted (default: 15)
            
        Returns:
            dict: Result with count of deleted files and list of deleted filenames
        """
        try:
            deleted_count = 0
            deleted_files = []
            current_time = datetime.now()
            
            print(f"DEBUG cleanup_old_recycle_bin_files: Current time = {current_time}, threshold = {days} days")
            
            # Iterate through all files in recycle bin
            for filename in os.listdir(self.recycle_bin_directory):
                file_path = os.path.join(self.recycle_bin_directory, filename)
                
                # Skip if not a file
                if not os.path.isfile(file_path):
                    continue
                
                # Get file modification time (when it was moved to recycle bin)
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Calculate age in days
                age_days = (current_time - file_mtime).days
                
                print(f"DEBUG: File '{filename}' - mtime: {file_mtime}, age: {age_days} days")
                
                # Delete if older than specified days
                if age_days >= days:
                    os.remove(file_path)
                    deleted_count += 1
                    deleted_files.append(filename)
                    print(f"Auto-deleted: {filename} (age: {age_days} days)")
                else:
                    print(f"Keeping: {filename} (age: {age_days} days < {days} days threshold)")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "deleted_files": deleted_files
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to cleanup recycle bin: {str(e)}"
            }
    
    def get_recycle_bin_file_age(self, recycle_filename):
        """
        Get the age of a file in the recycle bin in days.
        
        Args:
            recycle_filename (str): Filename in recycle bin
            
        Returns:
            int: Age in days, or None if file not found
        """
        try:
            recycle_path = os.path.join(self.recycle_bin_directory, recycle_filename)
            if os.path.exists(recycle_path):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(recycle_path))
                age_days = (datetime.now() - file_mtime).days
                return age_days
            return None
        except Exception as e:
            print(f"Error getting file age: {str(e)}")
            return None
    
    def delete_file(self, relative_path):
        """
        Delete a file from storage (deprecated - use move_to_recycle_bin instead).
        
        Args:
            relative_path (str): Relative path in storage
            
        Returns:
            dict: Result with success status and optional error message
        """
        try:
            full_path = self.get_file_path(relative_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": "File not found"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete file: {str(e)}"
            }
    
    def file_exists(self, relative_path):
        """
        Check if a file exists in storage.
        
        Args:
            relative_path (str): Relative path in storage
            
        Returns:
            bool: True if file exists, False otherwise
        """
        full_path = self.get_file_path(relative_path)
        return os.path.exists(full_path)
    
    def check_duplicate_filename(self, filename):
        """
        Check if a filename already exists in the uploaded files.
        
        Args:
            filename (str): Filename to check (without extension)
            
        Returns:
            bool: True if duplicate exists, False otherwise
        """
        from ..Mock.data_loader import get_uploaded_files
        
        uploaded_files = get_uploaded_files()
        for file_data in uploaded_files:
            if file_data.get('filename') == filename:
                return True
        return False
    
    def generate_unique_filename(self, base_name):
        """
        Generate a unique filename by adding (#) suffix if duplicate exists.
        
        Args:
            base_name (str): Base filename (without extension)
            
        Returns:
            str: Unique filename with (#) suffix if needed
        """
        from ..Mock.data_loader import get_uploaded_files
        
        uploaded_files = get_uploaded_files()
        existing_names = {file_data.get('filename') for file_data in uploaded_files}
        
        # If no duplicate, return original
        if base_name not in existing_names:
            return base_name
        
        # Find the next available number
        counter = 1
        while True:
            new_name = f"{base_name} ({counter})"
            if new_name not in existing_names:
                return new_name
            counter += 1
