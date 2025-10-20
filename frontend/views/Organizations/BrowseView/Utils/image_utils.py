"""
Utility module for secure image handling in the organization system.
Handles image validation, copying, and path resolution with organization-specific folders.
"""
import os
import shutil
import re
from pathlib import Path
from typing import Optional, Tuple

DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024


def ensure_data_directory() -> None:
    """Create the Data directory if it doesn't exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created Data directory at: {DATA_DIR}")


def ensure_org_directory(org_name: str) -> str:
    """
    Create an organization-specific directory within Data if it doesn't exist.
    
    Args:
        org_name: Name of the organization
        
    Returns:
        Path to the organization directory
    """
    ensure_data_directory()
    
    safe_org_name = sanitize_filename(org_name)
    safe_org_name = os.path.splitext(safe_org_name)[0]
    
    org_dir = os.path.join(DATA_DIR, safe_org_name)
    
    if not os.path.exists(org_dir):
        os.makedirs(org_dir)
        print(f"Created organization directory at: {org_dir}")
    
    return org_dir


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other security issues.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem use
    """
    filename = os.path.basename(filename)
    
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    filename = filename.replace(' ', '_')
    
    if not filename or filename == '.':
        filename = 'image.jpg'
    
    return filename


def validate_image_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate that the file is a legitimate image file.
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    try:
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            return False, f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
        
        if file_size == 0:
            return False, "File is empty"
    except OSError as e:
        return False, f"Error reading file: {str(e)}"
    
    try:
        with open(file_path, 'rb') as f:
            header = f.read(12)
            
            if header[:8] == b'\x89PNG\r\n\x1a\n':
                return True, ""
            elif header[:3] == b'\xff\xd8\xff':
                return True, ""
            elif header[:2] == b'BM':
                return True, ""
            elif header[:6] in (b'GIF87a', b'GIF89a'):
                return True, ""
            else:
                return False, "File does not appear to be a valid image"
    except Exception as e:
        return False, f"Error validating file: {str(e)}"


def copy_image_to_data(source_path: str, org_name: str) -> Optional[str]:
    """
    Copy an image file to the organization's Data subdirectory with validation and sanitization.
    
    Args:
        source_path: Path to the source image file
        org_name: Name of the organization (used to create subfolder)
        
    Returns:
        Relative path from Data directory (e.g., "CISC/logo.jpeg"), or None if failed
    """
    if source_path == "No Photo":
        return "No Photo"
    
    is_valid, error_msg = validate_image_file(source_path)
    if not is_valid:
        print(f"Image validation failed: {error_msg}")
        return None
    
    org_dir = ensure_org_directory(org_name)
    
    original_filename = os.path.basename(source_path)
    safe_filename = sanitize_filename(original_filename)
    
    destination_path = os.path.join(org_dir, safe_filename)
    if os.path.exists(destination_path):
        name, ext = os.path.splitext(safe_filename)
        counter = 1
        while os.path.exists(destination_path):
            safe_filename = f"{name}_{counter}{ext}"
            destination_path = os.path.join(org_dir, safe_filename)
            counter += 1
    
    try:
        shutil.copy2(source_path, destination_path)
        print(f"Copied image to: {destination_path}")
        
        safe_org_name = sanitize_filename(org_name)
        safe_org_name = os.path.splitext(safe_org_name)[0]
        return f"{safe_org_name}/{safe_filename}"
    except Exception as e:
        print(f"Error copying image: {str(e)}")
        return None


def get_image_path(relative_path: str) -> str:
    """
    Resolve the full path to an image in the Data directory.
    
    Args:
        relative_path: Relative path from Data directory (e.g., "CISC/logo.jpeg" or just "logo.jpeg")
        
    Returns:
        Full absolute path to the image, or the relative_path if it doesn't exist
    """
    if relative_path == "No Photo" or not relative_path:
        return "No Photo"
    
    full_path = os.path.join(DATA_DIR, relative_path)
    
    if os.path.exists(full_path):
        return full_path
    else:
        print(f"Warning: Image file not found: {full_path}")
        return relative_path


def delete_image(relative_path: str) -> bool:
    """
    Delete an image from the Data directory.
    
    Args:
        relative_path: Relative path from Data directory (e.g., "CISC/logo.jpeg")
        
    Returns:
        True if deleted successfully, False otherwise
    """
    if relative_path == "No Photo" or not relative_path:
        return False
    
    file_path = os.path.join(DATA_DIR, relative_path)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted image: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error deleting image: {str(e)}")
        return False
