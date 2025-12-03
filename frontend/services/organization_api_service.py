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
    def fetch_organizations(search_query: Optional[str] = None, role: Optional[str] = None, include_archived: bool = False) -> Dict:
        """
        Fetch all organizations from the database or search by query
        
        Args:
            search_query: Optional search term to filter organizations
            role: User role ('admin' to see all, otherwise only active & non-archived)
            include_archived: If True and role is admin, only fetch archived orgs
        
        Returns:
            Dictionary containing the API response with list of organizations
        """
        url = f"{OrganizationAPIService.BASE_URL}/"
        
        # Add query parameters
        params = {}
        if search_query:
            params['search'] = search_query
        if role:
            params['role'] = role
        if include_archived:
            params['include_archived'] = 'true'
        
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
        main_org_ids: Optional[list] = None,
        created_by_id: Optional[int] = None
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
            created_by_id: BaseUser ID of user creating the org (optional, for logging)
            
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
            "is_active": True,  # Ensure organization is active when created
        }
        
        # Add objectives if provided
        if objectives:
            data["objectives"] = objectives
        
        # Add main_org if provided
        if main_org_ids:
            data["main_org"] = main_org_ids
        
        # Add created_by_id for logging
        if created_by_id:
            data["created_by_id"] = created_by_id
        
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
        main_org_ids: Optional[list] = None,
        updated_by_id: Optional[int] = None
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
            updated_by_id: BaseUser ID of user updating the org (optional, for logging)
            
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
        if updated_by_id is not None:
            data["updated_by_id"] = updated_by_id
        
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
    def process_application(application_id: int, action: str, admin_user_id: Optional[int] = None) -> Dict:
        """
        Accept or reject a membership application
        
        Args:
            application_id: The application ID
            action: 'accept' or 'reject'
            admin_user_id: BaseUser ID of admin performing the action (optional, for logging)
            
        Returns:
            Dictionary containing the API response
        """
        url = f"{OrganizationAPIService.BASE_URL}/applications/{application_id}/action/"
        
        data = {
            "action": action
        }
        
        # Add admin_user_id for logging
        if admin_user_id:
            data["admin_user_id"] = admin_user_id
        
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
    def update_member_position(member_id: int, position_id=None, position_name=None, 
                               start_term=None, end_term=None, updated_by_id=None, photo=None) -> Dict:
        """
        Update a member's position
        
        Args:
            member_id: The OrganizationMembers ID
            position_id: The Positions ID (None for regular member)
            position_name: The position name (for backwards compatibility)
            start_term: Start date in YYYY-MM-DD format (required for officers)
            end_term: End date in YYYY-MM-DD format (optional)
            updated_by_id: BaseUser ID of user making the update (optional)
            photo: Path to photo file to upload (optional)
            
        Returns:
            Dictionary containing the API response
        """
        url = f"{OrganizationAPIService.BASE_URL}/members/{member_id}/position/"
        
        # Build position_data dict from parameters
        position_data = {
            'position_id': position_id,
            'position_name': position_name,
            'start_term': start_term,
            'end_term': end_term,
            'updated_by_id': updated_by_id,
            'photo': photo
        }
        
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
    
    @staticmethod
    def get_student_joined_organizations(student_id: int) -> Dict:
        """
        Get all organizations that a student has joined (is a member of)
        
        Args:
            student_id: StudentProfile ID of the student
            
        Returns:
            Dictionary containing the API response with list of joined organizations
        """
        url = f"{OrganizationAPIService.BASE_URL}/students/{student_id}/joined/"
        
        print(f"DEBUG API Service: Calling {url} with student_id={student_id}")
        
        try:
            response = requests.get(url, timeout=10)
            
            print(f"DEBUG API Service: Response status={response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"DEBUG API Service: Success response data: {response_data}")
                return {
                    'success': True,
                    'data': response_data.get('data', []),
                    'message': response_data.get('message', 'Joined organizations retrieved successfully'),
                    'count': response_data.get('count', 0)
                }
            else:
                error_data = response.json() if response.text else {}
                print(f"DEBUG API Service: Error response: {error_data}")
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error'),
                    'message': error_data.get('message', 'Failed to retrieve joined organizations'),
                    'status_code': response.status_code
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Network error: {str(e)}'
            }
    
    @staticmethod
    def get_organization_members(org_id: int) -> Dict:
        """
        Get all members of an organization
        
        Args:
            org_id: Organization ID
            
        Returns:
            Dictionary containing the API response with list of members
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
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error'),
                    'message': error_data.get('message', 'Failed to retrieve members'),
                    'status_code': response.status_code
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Network error: {str(e)}'
            }

    @staticmethod
    def get_logs(action: Optional[str] = None, target_type: Optional[str] = None, 
                 user_id: Optional[int] = None, limit: int = 100) -> Dict:
        """
        Get organization action logs with optional filters
        
        Args:
            action: Filter by action type (created, edited, kicked, accepted, rejected, applied, archived)
            target_type: Filter by target type (Organization, OrganizationMembers, MembershipApplication, etc.)
            user_id: Filter by user who performed the action
            limit: Maximum number of logs to return (default: 100)
            
        Returns:
            Dictionary containing the API response with list of logs
        """
        url = f"{OrganizationAPIService.BASE_URL}/logs/"
        
        params = {'limit': limit}
        if action:
            params['action'] = action
        if target_type:
            params['target_type'] = target_type
        if user_id:
            params['user_id'] = user_id
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', []),
                    'message': response_data.get('message', 'Logs retrieved successfully'),
                    'count': response_data.get('count', 0)
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error'),
                    'message': error_data.get('message', 'Failed to retrieve logs'),
                    'status_code': response.status_code
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Network error: {str(e)}'
            }

    @staticmethod
    def get_logs_for_target(target_type: str, target_id: int) -> Dict:
        """
        Get all logs for a specific target (e.g., all logs for Organization #5)
        
        Args:
            target_type: The type of target (e.g., 'Organization', 'OrganizationMembers')
            target_id: The ID of the target
            
        Returns:
            Dictionary containing the API response with list of logs
        """
        url = f"{OrganizationAPIService.BASE_URL}/logs/{target_type}/{target_id}/"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', []),
                    'message': response_data.get('message', 'Logs retrieved successfully'),
                    'count': response_data.get('count', 0)
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error'),
                    'message': error_data.get('message', 'Failed to retrieve logs'),
                    'status_code': response.status_code
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Network error: {str(e)}'
            }

    @staticmethod
    def archive_organization(org_id: int, admin_user_id: Optional[int] = None) -> Dict:
        """
        Archive an organization (cannot be retrieved after archiving)
        
        Args:
            org_id: The organization ID to archive
            admin_user_id: BaseUser ID of admin performing the action (for logging)
            
        Returns:
            Dictionary containing the API response
        """
        url = f"{OrganizationAPIService.BASE_URL}/{org_id}/archive/"
        
        data = {}
        if admin_user_id:
            data['admin_user_id'] = admin_user_id
        
        try:
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', {}),
                    'message': response_data.get('message', 'Organization archived successfully')
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error'),
                    'message': error_data.get('message', 'Failed to archive organization'),
                    'status_code': response.status_code
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Network error: {str(e)}'
            }

    @staticmethod
    def toggle_organization_active(org_id: int, admin_user_id: Optional[int] = None) -> Dict:
        """
        Toggle an organization's active status (activate/deactivate)
        
        Args:
            org_id: The organization ID
            admin_user_id: BaseUser ID of admin performing the action (for logging)
            
        Returns:
            Dictionary containing the API response with new is_active status
        """
        url = f"{OrganizationAPIService.BASE_URL}/{org_id}/toggle-active/"
        
        data = {}
        if admin_user_id:
            data['admin_user_id'] = admin_user_id
        
        try:
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', {}),
                    'message': response_data.get('message', 'Organization status updated successfully'),
                    'is_active': response_data.get('is_active', False)
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error'),
                    'message': error_data.get('message', 'Failed to update organization status'),
                    'status_code': response.status_code
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Network error: {str(e)}'
            }

    @staticmethod
    def get_faculty_list() -> Dict:
        """
        Get all faculty members for adviser selection dropdown
        
        Returns:
            Dictionary containing the API response with list of faculty
        """
        url = f"{OrganizationAPIService.BASE_URL}/faculty/"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', []),
                    'message': response_data.get('message', 'Faculty list retrieved successfully'),
                    'count': response_data.get('count', 0)
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error'),
                    'message': error_data.get('message', 'Failed to retrieve faculty list'),
                    'status_code': response.status_code
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Network error: {str(e)}'
            }

    @staticmethod
    def get_faculty_advised_organizations(username: str, search_query: Optional[str] = None) -> Dict:
        """
        Get all organizations that a faculty member advises
        
        Args:
            username: The faculty's username
            search_query: Optional search term to filter organizations
            
        Returns:
            Dictionary containing the API response with list of advised organizations
        """
        url = f"{OrganizationAPIService.BASE_URL}/faculty/advised/"
        
        params = {'username': username}
        if search_query:
            params['search'] = search_query
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', []),
                    'message': response_data.get('message', 'Advised organizations retrieved successfully'),
                    'count': response_data.get('count', 0)
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error'),
                    'message': error_data.get('message', 'Failed to retrieve advised organizations'),
                    'status_code': response.status_code
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Network error: {str(e)}'
            }

    @staticmethod
    def get_organization_advisers(org_id: int) -> Dict:
        """
        Get all advisers for a specific organization
        
        Args:
            org_id: The organization ID
            
        Returns:
            Dictionary containing the API response with list of advisers
        """
        url = f"{OrganizationAPIService.BASE_URL}/{org_id}/advisers/"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', []),
                    'message': response_data.get('message', 'Advisers retrieved successfully'),
                    'count': response_data.get('count', 0)
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error'),
                    'message': error_data.get('message', 'Failed to retrieve advisers'),
                    'status_code': response.status_code
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Network error: {str(e)}'
            }

    @staticmethod
    def add_organization_adviser(org_id: int, adviser_id: int, role: str = 'pri', start_date: str = None, end_date: str = None) -> Dict:
        """
        Add an adviser to an organization
        
        Args:
            org_id: The organization ID
            adviser_id: The FacultyProfile ID of the adviser
            role: 'pri' for Primary, 'sec' for Secondary (default: 'pri')
            start_date: Start date of the adviser term (YYYY-MM-DD format, required)
            end_date: End date of the adviser term (YYYY-MM-DD format, optional)
            
        Returns:
            Dictionary containing the API response
        """
        url = f"{OrganizationAPIService.BASE_URL}/{org_id}/advisers/"
        
        data = {
            'adviser_id': adviser_id,
            'role': role,
            'start_date': start_date,
            'end_date': end_date
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 201:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', {}),
                    'message': response_data.get('message', 'Adviser added successfully')
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error'),
                    'message': error_data.get('message', 'Failed to add adviser'),
                    'status_code': response.status_code
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Network error: {str(e)}'
            }

    @staticmethod
    def remove_organization_adviser(org_id: int, adviser_term_id: int) -> Dict:
        """
        Remove an adviser from an organization
        
        Args:
            org_id: The organization ID
            adviser_term_id: The OrgAdviserTerm ID to remove
            
        Returns:
            Dictionary containing the API response
        """
        url = f"{OrganizationAPIService.BASE_URL}/{org_id}/advisers/"
        
        data = {
            'adviser_term_id': adviser_term_id
        }
        
        try:
            response = requests.delete(url, json=data, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    'success': True,
                    'message': response_data.get('message', 'Adviser removed successfully')
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error'),
                    'message': error_data.get('message', 'Failed to remove adviser'),
                    'status_code': response.status_code
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Network error: {str(e)}'
            }

    @staticmethod
    def update_organization_adviser(org_id: int, adviser_term_id: int, role: Optional[str] = None) -> Dict:
        """
        Update an adviser's role for an organization
        
        Args:
            org_id: The organization ID
            adviser_term_id: The OrgAdviserTerm ID to update
            role: New role ('pri' or 'sec')
            
        Returns:
            Dictionary containing the API response
        """
        url = f"{OrganizationAPIService.BASE_URL}/{org_id}/advisers/{adviser_term_id}/"
        
        data = {}
        if role:
            data['role'] = role
        
        try:
            response = requests.put(url, json=data, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    'success': True,
                    'data': response_data.get('data', {}),
                    'message': response_data.get('message', 'Adviser updated successfully')
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': error_data.get('message', 'Unknown error'),
                    'message': error_data.get('message', 'Failed to update adviser'),
                    'status_code': response.status_code
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Network error: {str(e)}'
            }