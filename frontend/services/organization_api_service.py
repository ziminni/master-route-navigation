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
    def fetch_organizations(search_query: Optional[str] = None) -> Dict:
        """
        Fetch all organizations from the database or search by query
        
        Args:
            search_query: Optional search term to filter organizations
        
        Returns:
            Dictionary containing the API response with list of organizations
        """
        url = f"{OrganizationAPIService.BASE_URL}/"
        
        # Add search query parameter if provided
        params = {}
        if search_query:
            params['search'] = search_query
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', []),
                    'message': response_data.get('message', 'Organizations fetched successfully'),
                    'count': response_data.get('count', 0)
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
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', {}),
                    'message': response_data.get('message', 'Organization details fetched successfully')
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
        objectives: Optional[str] = None,
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
            objectives: Organization objectives (optional)
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
        
        # Add objectives if provided
        if objectives:
            data["objectives"] = objectives
        
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
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', {}),
                    'message': response_data.get('message', 'Organization created successfully')
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
        objectives: Optional[str] = None,
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
            objectives: Organization objectives (optional)
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
        if objectives is not None:
            data["objectives"] = objectives
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
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', {}),
                    'message': response_data.get('message', 'Organization updated successfully')
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
    
    @staticmethod
    def get_student_application_statuses(user_id: int) -> Dict:
        """
        Get all application statuses for a student
        
        Args:
            user_id: The student's user ID
            
        Returns:
            Dictionary containing application statuses for each organization
        """
        url = f"{OrganizationAPIService.BASE_URL}/applications/{user_id}/"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', {}),
                    'message': response_data.get('message', 'Application statuses retrieved successfully')
                }
            else:
                return {
                    'success': False,
                    'error': response.json() if response.text else 'Unknown error',
                    'message': 'Failed to retrieve application statuses',
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
    def get_organization_applicants(org_id: int) -> Dict:
        """
        Get all pending applicants for a specific organization
        
        Args:
            org_id: The organization ID
            
        Returns:
            Dictionary containing list of applicants
        """
        url = f"{OrganizationAPIService.BASE_URL}/{org_id}/applicants/"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', []),
                    'count': response_data.get('count', 0),
                    'message': response_data.get('message', 'Applicants retrieved successfully')
                }
            else:
                return {
                    'success': False,
                    'error': response.json() if response.text else 'Unknown error',
                    'message': 'Failed to retrieve applicants',
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
    def process_application(application_id: int, action: str) -> Dict:
        """
        Accept or reject a membership application
        
        Args:
            application_id: The application ID
            action: 'accept' or 'reject'
            
        Returns:
            Dictionary containing the API response
        """
        url = f"{OrganizationAPIService.BASE_URL}/applications/{application_id}/action/"
        
        data = {
            "action": action
        }
        
        try:
            response = requests.put(url, json=data, timeout=10)
            
            print(f"DEBUG: Response status code: {response.status_code}")
            print(f"DEBUG: Response text: {response.text}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    return {
                        'success': True,
                        'data': response_data.get('data', {}),
                        'message': response_data.get('message', f'Application {action}ed successfully')
                    }
                except ValueError as e:
                    print(f"DEBUG: JSON decode error - {str(e)}")
                    return {
                        'success': False,
                        'error': f'Invalid JSON response: {str(e)}',
                        'message': f'Server returned invalid response'
                    }
            else:
                try:
                    error_data = response.json() if response.text else {}
                except ValueError:
                    error_data = {'message': response.text}
                    
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error'),
                    'message': error_data.get('message', f'Failed to {action} application'),
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
    def get_organization_members(org_id: int) -> Dict:
        """
        Get all active members for a specific organization
        
        Args:
            org_id: The organization ID
            
        Returns:
            Dictionary containing list of members
        """
        url = f"{OrganizationAPIService.BASE_URL}/{org_id}/members/"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', []),
                    'message': response_data.get('message', 'Members retrieved successfully')
                }
            else:
                return {
                    'success': False,
                    'error': response.json() if response.text else 'Unknown error',
                    'message': 'Failed to retrieve members',
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
    def submit_membership_application(user_id: int, organization_id: int) -> Dict:
        """
        Submit a membership application to an organization
        
        Args:
            user_id: The student's user ID
            organization_id: The organization ID to apply to
            
        Returns:
            Dictionary containing the API response
        """
        url = f"{OrganizationAPIService.BASE_URL}/apply/"
        
        data = {
            "user_id": user_id,
            "organization_id": organization_id
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 201:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', {}),
                    'message': response_data.get('message', 'Application submitted successfully')
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': error_data.get('errors', error_data.get('message', 'Unknown error')),
                    'message': error_data.get('message', 'Failed to submit application'),
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
    def get_member_term_data(member_id: int) -> dict:
        """
        Get current officer term data for a member.
        
        Args:
            member_id: OrganizationMembers ID
            
        Returns:
            dict with success, message, and data (position_id, position_name, start_term, end_term)
        """
        try:
            url = f"{OrganizationAPIService.BASE_URL}/members/{member_id}/position/"
            print(f"DEBUG: Fetching member term data from {url}")
            
            response = requests.get(url, timeout=10)
            print(f"DEBUG: Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"DEBUG: Member term data: {data}")
                return data
            else:
                print(f"ERROR: Failed to get member term data - Status {response.status_code}")
                return {
                    'success': False,
                    'message': f'Server returned status {response.status_code}'
                }
                
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Network error getting member term data: {e}")
            return {
                'success': False,
                'message': f'Network error: {str(e)}'
            }
        except Exception as e:
            print(f"ERROR: Unexpected error getting member term data: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }

    @staticmethod
    def get_positions() -> Dict:
        """
        Get all available positions from the database
        
        Returns:
            Dictionary containing list of positions
        """
        url = f"{OrganizationAPIService.BASE_URL}/positions/"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', []),
                    'message': response_data.get('message', 'Positions retrieved successfully')
                }
            else:
                return {
                    'success': False,
                    'error': response.json() if response.text else 'Unknown error',
                    'message': 'Failed to retrieve positions',
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
    def get_current_user_by_username(username: str) -> Dict:
        """
        Get current user profile ID by username
        
        Args:
            username: The username of the logged-in user
            
        Returns:
            Dictionary containing user data with profile_id and profile_type
        """
        url = f"{OrganizationAPIService.BASE_URL}/current-user/"
        
        params = {'username': username}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', {}),
                    'message': response_data.get('message', 'User retrieved successfully')
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error'),
                    'message': error_data.get('message', 'Failed to retrieve user'),
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
    def update_member_position(member_id: int, position_data: Dict) -> Dict:
        """
        Update a member's position
        
        Args:
            member_id: The OrganizationMembers ID
            position_data: Dict containing:
                - position_id: The Positions ID (None for regular member)
                - position_name: The position name (for backwards compatibility)
                - start_term: Start date in YYYY-MM-DD format (required for officers)
                - end_term: End date in YYYY-MM-DD format (optional)
                - updated_by_id: StudentProfile ID of user making the update (optional)
                - photo: Path to photo file to upload (optional)
            
        Returns:
            Dictionary containing the API response
        """
        url = f"{OrganizationAPIService.BASE_URL}/members/{member_id}/position/"
        
        # Check if we need to send as multipart/form-data (for photo upload)
        photo_path = position_data.get('photo')
        
        try:
            if photo_path:
                # Send as multipart/form-data
                files = {}
                data = {}
                
                try:
                    files['photo'] = open(photo_path, 'rb')
                    data = {k: v for k, v in position_data.items() if k != 'photo' and v is not None}
                    
                    response = requests.put(url, data=data, files=files, timeout=10)
                finally:
                    if 'photo' in files:
                        files['photo'].close()
            else:
                # Send as JSON, filter out None values
                json_data = {k: v for k, v in position_data.items() if v is not None}
                response = requests.put(url, json=json_data, timeout=10)
            
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response content-type: {response.headers.get('content-type', 'unknown')}")
            # Check if response is JSON
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type:
                print(f"ERROR: Backend returned non-JSON response (content-type: {content_type})")
                print(f"ERROR: Response text preview: {response.text[:500]}")
                return {
                    'success': False,
                    'error': 'Server Error',
                    'message': f'Backend server error. Check backend logs for details. Status: {response.status_code}'
                }
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                except ValueError as json_err:
                    print(f"ERROR: JSON decode failed: {json_err}")
                    print(f"ERROR: Full response text: {response.text}")
                    return {
                        'success': False,
                        'error': 'Invalid JSON response from server',
                        'message': f'Server returned invalid JSON: {str(json_err)}'
                    }
                    
                return {
                    'success': True,
                    'data': response_data.get('data', {}),
                    'message': response_data.get('message', 'Member position updated successfully')
                }
            else:
                try:
                    error_data = response.json() if response.text else {}
                except ValueError:
                    error_data = {'message': response.text[:200] if response.text else 'Unknown error'}
                    
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error'),
                    'message': error_data.get('message', 'Failed to update member position'),
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
    def kick_member(member_id: int, username: str) -> Dict:
        """
        Kick/remove a member from the organization
        
        Args:
            member_id: ID of the OrganizationMember to kick
            username: Username of the admin performing the kick
            
        Returns:
            Dictionary containing the API response
        """
        url = f"{OrganizationAPIService.BASE_URL}/members/{member_id}/kick/?username={username}"
        
        try:
            response = requests.post(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                return {
                    'success': False,
                    'error': error_data.get('message', 'Failed to kick member'),
                    'message': error_data.get('message', f'Server returned status {response.status_code}')
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Network error: {str(e)}'
            }
