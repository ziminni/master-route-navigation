"""
Organization API Service
Handles all API calls to the backend for organization-related operations.
"""
import requests
import os
from typing import Dict, Optional


class OrganizationAPIService:
    """Service for handling organization API calls"""
    
    BASE_URL = "http://localhost:8000/api/organizations"
    
    @staticmethod
    def fetch_organizations() -> Dict:
        """
        Fetch all organizations from the database
        
        Returns:
            Dictionary containing the API response with list of organizations
        """
        url = f"{OrganizationAPIService.BASE_URL}/"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'message': 'Organizations fetched successfully'
                }
            else:
                return {
                    'success': False,
                    'error': response.json() if response.text else 'Unknown error',
                    'message': 'Failed to fetch organizations',
                    'status_code': response.status_code
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection Error',
                'message': 'Could not connect to the backend server. Please ensure the server is running.'
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Timeout Error',
                'message': 'Request timed out. Please try again.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'An unexpected error occurred: {str(e)}'
            }
    
    @staticmethod
    def fetch_organization_details(org_id: int) -> Dict:
        """
        Fetch detailed information for a specific organization
        
        Args:
            org_id: The organization ID
            
        Returns:
            Dictionary containing the API response with organization details
        """
        url = f"{OrganizationAPIService.BASE_URL}/{org_id}/"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'message': 'Organization details fetched successfully'
                }
            else:
                return {
                    'success': False,
                    'error': response.json() if response.text else 'Unknown error',
                    'message': 'Failed to fetch organization details',
                    'status_code': response.status_code
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection Error',
                'message': 'Could not connect to the backend server. Please ensure the server is running.'
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Timeout Error',
                'message': 'Request timed out. Please try again.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'An unexpected error occurred: {str(e)}'
            }
    
    @staticmethod
    def create_organization(
        name: str,
        description: str,
        org_level: str,
        logo_path: Optional[str] = None,
        status: str = "active",
        main_org_ids: Optional[list] = None
    ) -> Dict:
        """
        Create a new organization via API
        
        Args:
            name: Organization name
            description: Organization description
            org_level: Organization level ('col' for College, 'prog' for Program)
            logo_path: Path to logo file (optional)
            status: Organization status (default: 'active')
            main_org_ids: List of parent organization IDs (optional)
            
        Returns:
            Dictionary containing the API response
        """
        url = f"{OrganizationAPIService.BASE_URL}/create/"
        
        # Prepare data
        data = {
            "name": name,
            "description": description,
            "org_level": org_level,
            "status": status,
        }
        
        # Add main_org if provided
        if main_org_ids:
            data["main_org"] = main_org_ids
        
        # Handle file upload if logo_path is provided
        files = None
        if logo_path and os.path.exists(logo_path):
            try:
                files = {
                    'logo_path': open(logo_path, 'rb')
                }
            except Exception as e:
                print(f"Error opening logo file: {e}")
        
        try:
            # Make POST request
            if files:
                response = requests.post(url, data=data, files=files, timeout=10)
                # Close file after upload
                if files and 'logo_path' in files:
                    files['logo_path'].close()
            else:
                response = requests.post(url, json=data, timeout=10)
            
            # Check response status
            if response.status_code == 201:
                return {
                    'success': True,
                    'data': response.json(),
                    'message': 'Organization created successfully'
                }
            else:
                return {
                    'success': False,
                    'error': response.json() if response.text else 'Unknown error',
                    'message': 'Failed to create organization',
                    'status_code': response.status_code
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection Error',
                'message': 'Could not connect to the backend server. Please ensure the server is running.'
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Timeout Error',
                'message': 'Request timed out. Please try again.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'An unexpected error occurred: {str(e)}'
            }
    
    @staticmethod
    def update_organization(
        org_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        org_level: Optional[str] = None,
        logo_path: Optional[str] = None,
        status: Optional[str] = None,
        main_org_ids: Optional[list] = None
    ) -> Dict:
        """
        Update an existing organization via API
        
        Args:
            org_id: The organization ID to update
            name: Organization name (optional)
            description: Organization description (optional)
            org_level: Organization level ('col' for College, 'prog' for Program) (optional)
            logo_path: Path to logo file (optional)
            status: Organization status (optional)
            main_org_ids: List of parent organization IDs (optional)
            
        Returns:
            Dictionary containing the API response
        """
        url = f"{OrganizationAPIService.BASE_URL}/{org_id}/"
        
        # Prepare data - only include fields that are provided
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if org_level is not None:
            data["org_level"] = org_level
        if status is not None:
            data["status"] = status
        if main_org_ids is not None:
            data["main_org"] = main_org_ids
        
        # Handle file upload if logo_path is provided
        files = None
        if logo_path and os.path.exists(logo_path):
            try:
                files = {
                    'logo_path': open(logo_path, 'rb')
                }
            except Exception as e:
                print(f"Error opening logo file: {e}")
        
        try:
            # Make PUT request
            if files:
                response = requests.put(url, data=data, files=files, timeout=10)
                # Close file after upload
                if files and 'logo_path' in files:
                    files['logo_path'].close()
            else:
                response = requests.put(url, json=data, timeout=10)
            
            # Check response status
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'message': 'Organization updated successfully'
                }
            else:
                return {
                    'success': False,
                    'error': response.json() if response.text else 'Unknown error',
                    'message': 'Failed to update organization',
                    'status_code': response.status_code
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection Error',
                'message': 'Could not connect to the backend server. Please ensure the server is running.'
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Timeout Error',
                'message': 'Request timed out. Please try again.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'An unexpected error occurred: {str(e)}'
            }
