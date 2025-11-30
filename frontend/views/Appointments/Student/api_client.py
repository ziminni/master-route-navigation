import requests
import json
import os
from datetime import datetime


class APIClient:
    BASE_URL = os.environ.get('API_BASE_URL', 'http://127.0.0.1:8000/api/appointments')
    
    def __init__(self, token=None):
        self.session = requests.Session()
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if token:
            headers['Authorization'] = f'Bearer {token}'
        self.session.headers.update(headers)

    # ===== APPOINTMENT METHODS =====
    
    def get_student_appointments(self):
        """Get appointments for the currently authenticated student"""
        try:
            response = self.session.get(f'{self.BASE_URL}/student_appointment_list/')
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching student appointments: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            return None

    def get_faculty_appointments(self):
        """Get appointments for the currently authenticated faculty"""
        try:
            response = self.session.get(f'{self.BASE_URL}/faculty_appointment_list/')
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching faculty appointments: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            return None

    def create_appointment(self, appointment_data):
        """
        Create a new appointment request (student only).
        
        Args:
            appointment_data (dict): Dictionary containing:
                - faculty (int): Faculty profile ID
                - start_at (str): ISO format datetime
                - end_at (str): ISO format datetime  
                - reason (str, optional): Reason for appointment
        
        Returns:
            dict: Created appointment data or None if failed
        """
        try:
            response = self.session.post(f'{self.BASE_URL}/create_appointment/', json=appointment_data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error creating appointment: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            return None

    def update_appointment(self, appointment_id, update_data):
        """
        Update an existing appointment.
        
        Args:
            appointment_id (int): ID of appointment to update
            update_data (dict): Fields to update. Can include:
                - status (str): New status ('approved', 'denied', 'canceled', 'completed')
                - start_at (str): New start time (ISO format) - triggers reschedule
                - end_at (str): New end time (ISO format) - triggers reschedule
        
        Returns:
            dict: Updated appointment data or None if failed
        """
        try:
            response = self.session.put(f'{self.BASE_URL}/update_appointment/{appointment_id}/', json=update_data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error updating appointment: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            return None

    # ===== AVAILABILITY METHODS =====
    def get_faculty_list(self):


        try:
            response = self.session.get(f'{self.BASE_URL}/faculty_appointment_list/')
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error creating appointment: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            return None

    
    def get_faculty_availability(self, faculty_id, date):
        """
        Get available time slots for a faculty member on a specific date.
        
        Args:
            faculty_id (int): Faculty profile ID
            date (str): Date in YYYY-MM-DD format
        
        Returns:
            list: Available time slots or None if failed
        """
        try:
            response = self.session.get(f'{self.BASE_URL}/faculty_availability/{faculty_id}/{date}/')
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching faculty availability: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            return None

    def create_availability_rule(self, rule_data):
        """
        Create an availability rule (faculty only).
        
        Args:
            rule_data (dict): Availability rule data including:
                - day_of_week (str): 'MON', 'TUE', etc.
                - start_time (str): HH:MM:SS format
                - end_time (str): HH:MM:SS format  
                - slot_minutes (int): Duration of each slot
        
        Returns:
            dict: Created rule data or None if failed
        """
        try:
            response = self.session.post(f'{self.BASE_URL}/create_availability/', json=rule_data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error creating availability rule: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            return None


    def get_faculties(self):

        try:
            response = self.session.get(f'{self.BASE_URL}/faculty_profiles/')
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error creating availability rule: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            return None


        





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


# ===== USAGE EXAMPLES =====

if __name__ == "__main__":
    # Initialize client with authentication token
    api = APIClient(token="your-auth-token-here")
    
    # Example 1: Student creates an appointment
    appointment_data = {
        "faculty": 1,
        "start_at": "2025-01-15T10:00:00",
        "end_at": "2025-01-15T10:30:00",
        "reason": "Project consultation"
    }
    result = api.create_appointment(appointment_data)
    print("Created appointment:", result)
    
    # Example 2: Faculty approves an appointment
    update_data = {
        "status": "approved"  # Can be: 'approved', 'denied', 'canceled', 'completed'
    }
    result = api.update_appointment(appointment_id=1, update_data=update_data)
    print("Updated appointment:", result)
    
    # Example 3: Student reschedules an appointment
    reschedule_data = {
        "start_at": "2025-01-15T14:00:00",
        "end_at": "2025-01-15T14:30:00"
    }
    result = api.update_appointment(appointment_id=1, update_data=reschedule_data)
    print("Rescheduled appointment:", result)
    
    # Example 4: Get available slots for a faculty
    availability = api.get_faculty_availability(faculty_id=1, date="2025-01-15")
    print("Available slots:", availability)
    
    # Example 5: Get student's appointments
    student_appointments = api.get_student_appointments()
    print("Student appointments:", student_appointments)
    
    # Example 6: Get faculty's appointments  
    faculty_appointments = api.get_faculty_appointments()
    print("Faculty appointments:", faculty_appointments)
    
    # Example 7: Faculty creates availability rule
    rule_data = {
        "day_of_week": "MON",
        "start_time": "09:00:00", 
        "end_time": "17:00:00",
        "slot_minutes": 30
    }
    result = api.create_availability_rule(rule_data)
    print("Created availability rule:", result)