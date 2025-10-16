"""
Documents Module Initializer

This module handles the initialization of JSON data files and default collections
when the Documents module is first accessed or when data files are missing.
"""

import json
import os
from datetime import datetime


def get_mock_data_directory():
    """
    Get the absolute path to the Mock data directory.
    
    Returns:
        str: Absolute path to the Mock directory
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return current_dir


def get_default_collections():
    """
    Get the default collections structure to be created on initialization.
    
    Returns:
        dict: Dictionary with collections array and next_collection_id counter
    """
    return {
        "collections": [
            {
                "id": 1,
                "name": "Syllabus",
                "icon": "folder1.png",
                "description": "Course syllabi and curriculum documents",
                "files": [],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": "system"
            },
            {
                "id": 2,
                "name": "Memo",
                "icon": "folder1.png",
                "description": "Official memorandums and announcements",
                "files": [],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": "system"
            },
            {
                "id": 3,
                "name": "Forms",
                "icon": "folder1.png",
                "description": "Administrative forms and templates",
                "files": [],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": "system"
            },
            {
                "id": 4,
                "name": "Others",
                "icon": "folder1.png",
                "description": "Miscellaneous documents and files",
                "files": [],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": "system"
            }
        ],
        "next_collection_id": 5  # Next available collection ID (4 default collections created)
    }


def get_default_files_data():
    """
    Get the default structure for files_data.json.
    
    Returns:
        dict: Default files data structure with unified files array
    """
    return {
        "files": [],
        "next_file_id": 1
    }


def get_default_storage_data():
    """
    Get the default structure for storage_data.json.
    
    Returns:
        dict: Default storage data structure
    """
    return {
        "total_size_gb": 100.0,
        "used_size_gb": 0.0,
        "free_size_gb": 100.0,
        "usage_percentage": 0
    }


def create_json_file(filepath, data):
    """
    Create a JSON file with the given data.
    
    Args:
        filepath (str): Full path to the JSON file
        data (dict or list): Data to write to the file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"✓ Created: {os.path.basename(filepath)}")
        return True
    except Exception as e:
        print(f"✗ Failed to create {os.path.basename(filepath)}: {e}")
        return False


def initialize_files_data():
    """
    Initialize files_data.json if it doesn't exist.
    
    Returns:
        bool: True if file was created or already exists
    """
    mock_dir = get_mock_data_directory()
    filepath = os.path.join(mock_dir, 'files_data.json')
    
    if os.path.exists(filepath):
        print(f"  files_data.json already exists")
        return True
    
    data = get_default_files_data()
    return create_json_file(filepath, data)


def initialize_collections_data():
    """
    Initialize collections_data.json with default collections if it doesn't exist.
    
    Returns:
        bool: True if file was created or already exists
    """
    mock_dir = get_mock_data_directory()
    filepath = os.path.join(mock_dir, 'collections_data.json')
    
    if os.path.exists(filepath):
        print(f"  collections_data.json already exists")
        return True
    
    # get_default_collections() now returns the complete structure with collections and next_collection_id
    data = get_default_collections()
    return create_json_file(filepath, data)


def initialize_storage_data():
    """
    Initialize storage_data.json if it doesn't exist.
    
    Returns:
        bool: True if file was created or already exists
    """
    mock_dir = get_mock_data_directory()
    filepath = os.path.join(mock_dir, 'storage_data.json')
    
    if os.path.exists(filepath):
        print(f"  storage_data.json already exists")
        return True
    
    data = get_default_storage_data()
    return create_json_file(filepath, data)


def initialize_documents_data():
    """
    Initialize all necessary JSON files for the Documents module.
    This function should be called when the Documents module is accessed.
    
    Returns:
        dict: Status of initialization
              {
                  "success": bool,
                  "files_created": list,
                  "message": str
              }
    """
    print("\n" + "="*50)
    print("Initializing Documents Module Data...")
    print("="*50)
    
    files_created = []
    all_success = True
    
    # Initialize files_data.json
    if initialize_files_data():
        files_created.append("files_data.json")
    else:
        all_success = False
    
    # Initialize collections_data.json with default collections
    if initialize_collections_data():
        files_created.append("collections_data.json")
    else:
        all_success = False
    
    # Initialize storage_data.json
    if initialize_storage_data():
        files_created.append("storage_data.json")
    else:
        all_success = False
    
    print("="*50)
    if all_success:
        print("✓ Documents module initialization complete!")
    else:
        print("⚠ Some files failed to initialize")
    print("="*50 + "\n")
    
    return {
        "success": all_success,
        "files_created": files_created,
        "message": "Initialization complete" if all_success else "Some files failed to initialize"
    }


def ensure_data_integrity():
    """
    Ensure all required JSON files exist and have valid structure.
    This is a convenience function that can be called to verify data integrity.
    
    Returns:
        bool: True if all files exist and are valid
    """
    mock_dir = get_mock_data_directory()
    required_files = [
        'files_data.json',
        'collections_data.json',
        'storage_data.json'
    ]
    
    all_valid = True
    for filename in required_files:
        filepath = os.path.join(mock_dir, filename)
        if not os.path.exists(filepath):
            print(f"Missing: {filename}")
            all_valid = False
        else:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError:
                print(f"Invalid JSON: {filename}")
                all_valid = False
    
    return all_valid


# Auto-initialize on module import (can be disabled if needed)
def auto_initialize():
    """
    Automatically initialize data files if they don't exist.
    This function is called when the module is imported.
    """
    if not ensure_data_integrity():
        initialize_documents_data()


if __name__ == "__main__":
    # Allow running this module directly for manual initialization
    initialize_documents_data()
