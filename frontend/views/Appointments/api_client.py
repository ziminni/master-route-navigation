import requests
import json
import os
import logging
from datetime import datetime

class APIClient:
    def __init__(self, token=None):
        self.base_url = "http://127.0.0.1:8000/api/appointments"
        self.session = requests.Session()
        
        # Set default headers first
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        
        # Add authentication if token provided
        if token:
            print(f"DEBUG: Initializing APIClient with token: {token[:20]}...")
            # Try different authentication methods
            self.token = token
            self.session.headers.update({
                'Authorization': f'Bearer {token}'
            })
    
    def _make_request(self, method, endpoint, **kwargs):
        """Helper method to make HTTP requests with error handling"""
        url = f'{self.base_url}{endpoint}' if endpoint.startswith('/') else f'{self.base_url}/{endpoint}'
        
        print(f"DEBUG: Making {method} request to: {url}")
        print(f"DEBUG: Headers: {self.session.headers}")
        
        try:
            response = self.session.request(method, url, **kwargs)
            print(f"DEBUG: Response status: {response.status_code}")
            
            if response.status_code == 200 or response.status_code == 201:
                return response.json()
            elif response.status_code == 401:
                print(f"DEBUG: Authentication failed for {url}")
                print(f"DEBUG: Response text: {response.text}")
                return None
            elif response.status_code == 404:
                print(f"DEBUG: Endpoint not found: {url}")
                return None
            else:
                print(f"DEBUG: Request failed with status {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            print(f"DEBUG: Connection error - is the server running at {self.base_url}?")
            return None
        except requests.exceptions.Timeout:
            print("DEBUG: Request timeout")
            return None
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON decode error: {e}")
            return None
        except Exception as e:
            print(f"DEBUG: Unexpected error: {e}")
            return None

    # ===== APPOINTMENT METHODS =====
    
    def get_student_appointments(self):
        """Get appointments for the currently authenticated student"""
        print(f"DEBUG: Getting student appointments with token: {self.token[:20] if self.token else 'No token'}")
        return self._make_request('GET', 'student_appointment_list/')

    def get_faculty_appointments(self):
        """Get appointments for the currently authenticated faculty"""
        return self._make_request('GET', 'faculty_appointment_list/')

    def create_appointment(self, appointment_data):
        """
        Create a new appointment request (student only).
        
        Args:
            appointment_data (dict): Dictionary containing:
                - faculty (int): Faculty profile ID
                - start_at (str): ISO format datetime
                - end_at (str): ISO format datetime  
                - additional_details (str): Reason for appointment
                - address (str): Meeting location
        """
        print(f"DEBUG: Creating appointment with data: {appointment_data}")
        return self._make_request('POST', 'create_appointment/', json=appointment_data)

    def update_appointment(self, appointment_id, update_data):
        """
        Update an existing appointment.
        
        Args:
            appointment_id (int): ID of appointment to update
            update_data (dict): Fields to update
        """
        return self._make_request('PUT', f'update_appointment/{appointment_id}/', json=update_data)

    # ===== AVAILABILITY METHODS =====
    
    def get_faculty_available_schedule(self, faculty_id, date):
        """
        Get available time slots for a faculty member on a specific date.
        
        Args:
            faculty_id (int): Faculty profile ID
            date (str): Date in YYYY-MM-DD format
        """
        return self._make_request('GET', f'available_schedule/{faculty_id}/{date}/')

    def create_availability_rule(self, data):
        """Create availability rule"""
        return self._make_request('POST', 'create_availability_rule/', json=data)

    def get_faculties(self):
        """Get all faculty profiles"""
        return self._make_request('GET', 'faculty_profiles/')
    def get_faculties(self):
        """Get all faculty profiles"""
        return self._make_request('GET', 'faculty_profiles/')

    def get_students(self):
        """Get all student profiles"""
        return self._make_request('GET', 'student_profiles/')

    def get_availability_rules(self, faculty_id=None, semester_id=None):
        """Get availability rules for faculty"""
        params = {}
        if faculty_id:
            params['faculty_id'] = faculty_id
        if semester_id:
            params['semester_id'] = semester_id
        return self._make_request('GET', 'get_availability_rule/', params=params)

    def get_all_appointments(self):
        """Get all appointments (admin only)"""
        return self._make_request('GET', 'all_appointment_list/')

    # ===== HELPER METHODS =====
    
    @staticmethod
    def format_datetime(dt):
        """Format datetime object to ISO format string"""
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    
    @staticmethod  
    def format_date(dt):
        """Format datetime/date object to YYYY-MM-DD string"""
        return dt.strftime("%Y-%m-%d")
    
    @staticmethod
    def format_time(dt):
        """Format datetime object to HH:MM:SS string"""
        return dt.strftime("%H:%M:%S")

    def test_authentication(self):
        """Test if authentication is working"""
        print("DEBUG: Testing authentication...")
        print(f"DEBUG: Base URL: {self.base_url}")
        print(f"DEBUG: Token: {self.token[:20] if self.token else 'No token'}...")
        print(f"DEBUG: Authorization Header: {self.session.headers.get('Authorization', 'Not set')}")
        
        # Make a simple test request
        result = self.get_student_appointments()
        if result is not None:
            print("DEBUG: Authentication successful!")
            return True
        else:
            print("DEBUG: Authentication failed!")
            return False

# ===== USAGE EXAMPLES =====

if __name__ == "__main__":
    # Test the APIClient
    token = "your-token-here"  # Replace with actual token from login
    api = APIClient(token=token)
    
    # Test authentication
    if api.test_authentication():
        print("API client initialized successfully!")
        
        # Test getting student appointments
        appointments = api.get_student_appointments()
        if appointments:
            print(f"Found {len(appointments)} appointments")
        else:
            print("No appointments found or error occurred")
    else:
        print("Failed to initialize API client. Check token and server.")