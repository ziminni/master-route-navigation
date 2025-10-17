"""
Test script to verify faculty workflow
This script tests the complete flow from student inquiry to faculty reply
"""

import sys
from PyQt6.QtWidgets import QApplication
from data_manager import DataManager

def test_faculty_workflow():
    """Test the complete faculty workflow"""
    print("🧪 Testing Faculty Workflow...")
    
    # Initialize data manager
    data_manager = DataManager()
    
    # Test 1: Check if faculty receives inquiries
    print("\n1. Checking faculty inquiries...")
    faculty_id = 4  # Kim Jong Un (faculty)
    inquiries = data_manager.get_inquiries_by_faculty(faculty_id)
    print(f"   Faculty {faculty_id} has {len(inquiries)} inquiries")
    
    for inquiry in inquiries:
        student = data_manager.get_user(inquiry.get('student_id'))
        print(f"   - Inquiry from {student.get('name', 'Unknown')}: {inquiry.get('subject', 'No Subject')}")
    
    # Test 2: Check if faculty can create messages
    print("\n2. Testing faculty message creation...")
    test_message = {
        'sender_id': faculty_id,
        'receiver_id': 2,  # Adolf Hitler (student)
        'subject': 'Re: Test Inquiry',
        'content': 'This is a test reply from faculty.',
        'priority': 'normal',
        'status': 'sent',
        'is_read': False
    }
    
    created_message = data_manager.create_message(test_message)
    if created_message:
        print(f"   ✅ Message created successfully! ID: {created_message['id']}")
    else:
        print("   ❌ Failed to create message")
    
    # Test 3: Check if faculty can update inquiry status
    print("\n3. Testing inquiry status update...")
    if inquiries:
        inquiry_id = inquiries[0]['id']
        updated = data_manager.update_inquiry(inquiry_id, {'status': 'in_progress'})
        if updated:
            print(f"   ✅ Inquiry {inquiry_id} status updated to 'in_progress'")
        else:
            print(f"   ❌ Failed to update inquiry {inquiry_id}")
    
    # Test 4: Check faculty message loading
    print("\n4. Testing faculty message loading...")
    faculty_messages = [m for m in data_manager.data['messages'] if m.get('receiver_id') == faculty_id]
    faculty_inquiries = data_manager.get_inquiries_by_faculty(faculty_id)
    
    print(f"   Faculty has {len(faculty_messages)} direct messages")
    print(f"   Faculty has {len(faculty_inquiries)} inquiries")
    
    total_items = len(faculty_messages) + len(faculty_inquiries)
    print(f"   Total items for faculty: {total_items}")
    
    if total_items > 0:
        print("   ✅ Faculty workflow is working correctly!")
    else:
        print("   ❌ Faculty workflow has issues - no items found")
    
    return total_items > 0

if __name__ == "__main__":
    success = test_faculty_workflow()
    if success:
        print("\n🎉 Faculty workflow test PASSED!")
    else:
        print("\n❌ Faculty workflow test FAILED!")
        sys.exit(1)
