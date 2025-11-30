with open(r'c:\Users\rbong\Desktop\school\CISCVHUB\master-route-navigation\frontend\services\organization_api_service.py', 'a') as f:
    f.write('''
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
''')
