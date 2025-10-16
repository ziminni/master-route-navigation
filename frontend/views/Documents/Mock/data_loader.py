"""
Data Loader Utility for Document Management System

This module provides functions to load mock data from JSON files
for the document management interface.
"""

import json
import os


def get_mock_data_path(filename):
    """
    Get the absolute path to a mock data file.
    
    Args:
        filename (str): Name of the JSON file (e.g., 'files_data.json')
        
    Returns:
        str: Absolute path to the JSON file
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, filename)


def load_json_data(filename):
    """
    Load data from a JSON file in the Mock folder with robust error handling.
    
    Args:
        filename (str): Name of the JSON file to load
        
    Returns:
        dict: Parsed JSON data with safe defaults
    """
    file_path = get_mock_data_path(filename)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            # Handle empty file
            if not content:
                print(f"Warning: Empty file '{filename}', using default structure")
                return _get_default_structure(filename)
            
            data = json.loads(content)
            # Handle empty JSON object or None
            if not data:
                return _get_default_structure(filename)
            return data
            
    except FileNotFoundError:
        print(f"Warning: Mock data file '{filename}' not found at {file_path}")
        print(f"Creating default structure for '{filename}'")
        return _get_default_structure(filename)
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in '{filename}': {e}")
        print(f"Using default structure for '{filename}'")
        return _get_default_structure(filename)
    except Exception as e:
        print(f"Unexpected error loading '{filename}': {e}")
        return _get_default_structure(filename)


def _get_default_structure(filename):
    """
    Get default structure based on filename.
    
    Args:
        filename (str): Name of the JSON file
        
    Returns:
        dict: Default structure for the file type
    """
    if 'collections' in filename.lower():
        return {"collections": []}
    elif 'files' in filename.lower():
        return {"files": [], "next_file_id": 1}
    elif 'storage' in filename.lower():
        return {
            "total_size_gb": 100.0,
            "used_size_gb": 0.0,
            "free_size_gb": 100.0,
            "usage_percentage": 0
        }
    else:
        return {}


def get_uploaded_files():
    """
    Load uploaded (active) files data from JSON with safe defaults.
    Filters files where is_deleted is False or not present.
    
    Returns:
        list: List of dictionaries containing file information
              [{"filename": str, "time": str, "extension": str, "is_deleted": False}, ...]
    """
    data = load_json_data('files_data.json')
    all_files = data.get('files', [])
    
    # Ensure it's a list
    if not isinstance(all_files, list):
        print("Warning: files is not a list, returning empty list")
        return []
    
    # Filter for non-deleted files
    uploaded_files = [f for f in all_files if not f.get('is_deleted', False)]
    return uploaded_files


def get_deleted_files():
    """
    Load deleted files data from JSON with safe defaults.
    Filters files where is_deleted is True.
    
    Returns:
        list: List of dictionaries containing deleted file information
              [{"filename": str, "time": str, "extension": str, "is_deleted": True}, ...]
    """
    data = load_json_data('files_data.json')
    all_files = data.get('files', [])
    
    # Ensure it's a list
    if not isinstance(all_files, list):
        print("Warning: files is not a list, returning empty list")
        return []
    
    # Filter for deleted files
    deleted_files = [f for f in all_files if f.get('is_deleted', False)]
    return deleted_files


def get_collections():
    """
    Load collections data from JSON with safe defaults.
    
    Returns:
        list: List of dictionaries containing collection information
              [{"id": int, "name": str, "icon": str, "files": [...]}, ...]
    """
    data = load_json_data('collections_data.json')
    
    # Handle both old format (direct array) and new format (with next_collection_id)
    if isinstance(data, list):
        # Old format: data is directly the collections array
        print("Warning: Old collections format detected (direct array). Consider migrating to new format.")
        return data
    
    # New format: data is a dict with 'collections' and 'next_collection_id'
    collections = data.get('collections', [])
    
    # Ensure it's a list
    if not isinstance(collections, list):
        print("Warning: collections is not a list, returning empty list")
        return []
    return collections


def get_collection_by_name(collection_name):
    """
    Get a specific collection by name.
    
    Args:
        collection_name (str): Name of the collection to retrieve
        
    Returns:
        dict: Collection data or None if not found
    """
    collections = get_collections()
    for collection in collections:
        if collection['name'] == collection_name:
            return collection
    return None


def get_storage_data():
    """
    Load storage usage data from JSON.
    
    Returns:
        dict: Dictionary containing storage information
              {"total_size_gb": float, "used_size_gb": float, 
               "free_size_gb": float, "usage_percentage": int}
    """
    return load_json_data('storage_data.json')


# Convenience function to get all data at once
def get_all_mock_data():
    """
    Load all mock data in a single call.
    
    Returns:
        dict: Dictionary containing all mock data
              {
                  "uploaded_files": [...],
                  "deleted_files": [...],
                  "collections": [...],
                  "storage": {...}
              }
    """
    return {
        "uploaded_files": get_uploaded_files(),
        "deleted_files": get_deleted_files(),
        "collections": get_collections(),
        "storage": get_storage_data()
    }
