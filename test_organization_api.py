"""
Simple test script to verify the Organization API is working.
Run this after starting the Django server (python manage.py runserver)
"""
import requests
import json


def test_list_organizations():
    """Test listing all organizations from database"""
    url = "http://localhost:8000/api/organizations/"
    
    print("Testing Organization List API...")
    print(f"URL: {url}")
    print("-" * 50)
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Message: {data.get('message')}")
            print(f"Count: {data.get('count')}")
            print(f"Organizations: {json.dumps(data.get('data', []), indent=2)}")
            print("\n✓ SUCCESS: Organizations retrieved successfully!")
            return True
        else:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            print("\n✗ FAILED: Failed to retrieve organizations")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to the server")
        print("Make sure the Django server is running: python manage.py runserver")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        return False


def test_create_organization():
    """Test creating an organization via API"""
    url = "http://localhost:8000/api/organizations/create/"
    
    # Test data
    data = {
        "name": "Test Organization",
        "description": "This is a test organization created via API",
        "org_level": "col",
        "status": "active",
        "main_org": []  # No main organization
    }
    
    print("Testing Organization Creation API...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=data, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("\n✓ SUCCESS: Organization created successfully!")
            return True
        else:
            print("\n✗ FAILED: Organization creation failed")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to the server")
        print("Make sure the Django server is running: python manage.py runserver")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        return False


def test_with_main_org():
    """Test creating an organization with main_org"""
    url = "http://localhost:8000/api/organizations/create/"
    
    # First, create a parent org
    parent_data = {
        "name": "Parent Organization",
        "description": "This is a parent organization",
        "org_level": "col",
        "status": "active"
    }
    
    print("\n\nCreating Parent Organization...")
    print("-" * 50)
    
    try:
        parent_response = requests.post(url, json=parent_data, timeout=10)
        
        if parent_response.status_code == 201:
            parent_id = parent_response.json()['data']['id']
            print(f"✓ Parent organization created with ID: {parent_id}")
            
            # Now create a child org under the parent
            child_data = {
                "name": "Child Organization",
                "description": "This is a child organization under parent",
                "org_level": "prog",
                "status": "active",
                "main_org": [parent_id]
            }
            
            print("\nCreating Child Organization with main_org...")
            print(f"Data: {json.dumps(child_data, indent=2)}")
            print("-" * 50)
            
            child_response = requests.post(url, json=child_data, timeout=10)
            
            print(f"Status Code: {child_response.status_code}")
            print(f"Response: {json.dumps(child_response.json(), indent=2)}")
            
            if child_response.status_code == 201:
                print("\n✓ SUCCESS: Child organization created with main_org!")
                return True
            else:
                print("\n✗ FAILED: Child organization creation failed")
                return False
        else:
            print("\n✗ FAILED: Parent organization creation failed")
            return False
            
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        return False


def test_validation():
    """Test validation - try to create org without required fields"""
    url = "http://localhost:8000/api/organizations/create/"
    
    # Invalid data - missing name
    data = {
        "description": "Test without name",
        "org_level": "col"
    }
    
    print("\n\nTesting Validation (should fail)...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=data, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400:
            print("\n✓ SUCCESS: Validation working correctly!")
            return True
        else:
            print("\n✗ UNEXPECTED: Expected 400 status code")
            return False
            
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Organization API Test Suite")
    print("=" * 50)
    
    # Run tests
    test0 = test_list_organizations()
    test1 = test_create_organization()
    test2 = test_validation()
    test3 = test_with_main_org()
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"  List Organizations: {'PASSED' if test0 else 'FAILED'}")
    print(f"  Create Organization: {'PASSED' if test1 else 'FAILED'}")
    print(f"  Validation: {'PASSED' if test2 else 'FAILED'}")
    print(f"  With Main Org: {'PASSED' if test3 else 'FAILED'}")
    print("=" * 50)
