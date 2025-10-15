"""
Data Manager Module for CISC Virtual Hub Messaging System
========================================================

This module handles all data operations (Create, Read, Update, Delete) 
for the messaging system using JSON files as a simple database.

Think of this as a digital filing cabinet that can:
- Store new information (Create)
- Find and retrieve information (Read) 
- Update existing information (Update)
- Remove information (Delete)
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union


class DataManager:
    """
    Main data manager class that handles all database operations.
    
    This is like a smart assistant that knows how to:
    - Open and read the data files
    - Find specific information you need
    - Add new information to the files
    - Update existing information
    - Remove information when needed
    """
    
    def __init__(self, data_file_path: str = "dummy_data.json"):
        """
        Initialize the data manager with the path to our data file.
        
        Args:
            data_file_path: The location of our JSON data file
                           (like telling the assistant where the filing cabinet is)
        """
        self.data_file_path = data_file_path
        self.data = self._load_data()  # Load all data when we start
    
    def _load_data(self) -> Dict[str, Any]:
        """
        Load all data from the JSON file into memory.
        
        This is like opening the filing cabinet and reading all the folders
        so we can quickly find information without opening the file every time.
        
        Returns:
            Dictionary containing all our data (users, messages, etc.)
        """
        try:
            # Try to open and read the JSON file
            with open(self.data_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            # If file doesn't exist, create empty data structure
            print(f"Data file {self.data_file_path} not found. Creating empty database.")
            return {
                "users": [],
                "messages": [],
                "inquiries": [],
                "notifications": [],
                "conversations": [],
                "departments": [],
                "message_categories": [],
                "priority_levels": [],
                "message_statuses": []
            }
        except json.JSONDecodeError:
            # If file is corrupted, create empty data structure
            print(f"Data file {self.data_file_path} is corrupted. Creating empty database.")
            return {
                "users": [],
                "messages": [],
                "inquiries": [],
                "notifications": [],
                "conversations": [],
                "departments": [],
                "message_categories": [],
                "priority_levels": [],
                "message_statuses": []
            }
    
    def _save_data(self) -> bool:
        """
        Save all data back to the JSON file.
        
        This is like putting all the folders back in the filing cabinet
        after we've made changes to them.
        
        Returns:
            True if save was successful, False if there was an error
        """
        try:
            # Write all data back to the JSON file
            with open(self.data_file_path, 'w', encoding='utf-8') as file:
                json.dump(self.data, file, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    # ========================================
    # USER MANAGEMENT FUNCTIONS
    # ========================================
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a new user to our system.
        
        This is like adding a new person's information card to our filing system.
        
        Args:
            user_data: Dictionary containing user information (name, email, role, etc.)
            
        Returns:
            The created user data with assigned ID, or None if creation failed
        """
        # Generate a new unique ID for this user
        # Find the highest existing ID and add 1
        max_id = max([user.get('id', 0) for user in self.data['users']], default=0)
        user_data['id'] = max_id + 1
        
        # Add current timestamp for when this user was created
        user_data['created_at'] = datetime.now().isoformat()
        
        # Add the new user to our list
        self.data['users'].append(user_data)
        
        # Save the changes to file
        if self._save_data():
            return user_data
        else:
            # If save failed, remove the user from memory
            self.data['users'].remove(user_data)
            return None
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Find and retrieve a specific user's information.
        
        This is like looking up someone's information card in our filing system.
        
        Args:
            user_id: The unique ID of the user we want to find
            
        Returns:
            The user's information if found, None if not found
        """
        # Look through all users to find one with matching ID
        for user in self.data['users']:
            if user.get('id') == user_id:
                return user
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Find a user by their email address.
        
        This is like looking up someone by their email instead of their ID number.
        
        Args:
            email: The email address to search for
            
        Returns:
            The user's information if found, None if not found
        """
        # Look through all users to find one with matching email
        for user in self.data['users']:
            if user.get('email') == email:
                return user
        return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get a list of all users in the system.
        
        This is like getting a complete directory of everyone in our filing system.
        
        Returns:
            List of all user information
        """
        return self.data['users'].copy()
    
    def update_user(self, user_id: int, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing user's information.
        
        This is like updating someone's information card with new details.
        
        Args:
            user_id: The ID of the user to update
            updated_data: New information to replace the old information
            
        Returns:
            The updated user data if successful, None if user not found
        """
        # Find the user in our list
        for i, user in enumerate(self.data['users']):
            if user.get('id') == user_id:
                # Update the user's information
                self.data['users'][i].update(updated_data)
                self.data['users'][i]['updated_at'] = datetime.now().isoformat()
                
                # Save changes to file
                if self._save_data():
                    return self.data['users'][i]
                else:
                    # If save failed, revert the changes
                    self.data['users'][i] = user
                    return None
        return None
    
    def delete_user(self, user_id: int) -> bool:
        """
        Remove a user from the system.
        
        This is like removing someone's information card from our filing system.
        
        Args:
            user_id: The ID of the user to remove
            
        Returns:
            True if user was deleted successfully, False if user not found
        """
        # Find and remove the user
        for i, user in enumerate(self.data['users']):
            if user.get('id') == user_id:
                del self.data['users'][i]
                # Save changes to file
                return self._save_data()
        return False
    
    # ========================================
    # MESSAGE MANAGEMENT FUNCTIONS
    # ========================================
    
    def create_message(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a new message to our system.
        
        This is like adding a new letter to our message filing system.
        
        Args:
            message_data: Dictionary containing message information (sender, receiver, content, etc.)
            
        Returns:
            The created message data with assigned ID, or None if creation failed
        """
        # Generate a new unique ID for this message
        max_id = max([msg.get('id', 0) for msg in self.data['messages']], default=0)
        message_data['id'] = max_id + 1
        
        # Add current timestamp for when this message was created
        message_data['created_at'] = datetime.now().isoformat()
        message_data['updated_at'] = datetime.now().isoformat()
        
        # Add the new message to our list
        self.data['messages'].append(message_data)
        
        # Save the changes to file
        if self._save_data():
            return message_data
        else:
            # If save failed, remove the message from memory
            self.data['messages'].remove(message_data)
            return None
    
    def get_message(self, message_id: int) -> Optional[Dict[str, Any]]:
        """
        Find and retrieve a specific message.
        
        This is like looking up a specific letter in our message filing system.
        
        Args:
            message_id: The unique ID of the message to find
            
        Returns:
            The message information if found, None if not found
        """
        # Look through all messages to find one with matching ID
        for message in self.data['messages']:
            if message.get('id') == message_id:
                return message
        return None
    
    def get_messages_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all messages for a specific user (both sent and received).
        
        This is like getting all letters that belong to a specific person.
        
        Args:
            user_id: The ID of the user whose messages we want
            
        Returns:
            List of all messages for this user
        """
        user_messages = []
        # Look through all messages to find ones involving this user
        for message in self.data['messages']:
            if (message.get('sender_id') == user_id or 
                message.get('receiver_id') == user_id):
                user_messages.append(message)
        return user_messages
    
    def get_messages_by_conversation(self, sender_id: int, receiver_id: int) -> List[Dict[str, Any]]:
        """
        Get all messages between two specific users.
        
        This is like getting all letters exchanged between two specific people.
        
        Args:
            sender_id: The ID of one user in the conversation
            receiver_id: The ID of the other user in the conversation
            
        Returns:
            List of all messages between these two users
        """
        conversation_messages = []
        # Look through all messages to find ones between these two users
        for message in self.data['messages']:
            if ((message.get('sender_id') == sender_id and message.get('receiver_id') == receiver_id) or
                (message.get('sender_id') == receiver_id and message.get('receiver_id') == sender_id)):
                conversation_messages.append(message)
        return conversation_messages
    
    def update_message(self, message_id: int, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing message.
        
        This is like updating a letter with new information (like marking it as read).
        
        Args:
            message_id: The ID of the message to update
            updated_data: New information to replace the old information
            
        Returns:
            The updated message data if successful, None if message not found
        """
        # Find the message in our list
        for i, message in enumerate(self.data['messages']):
            if message.get('id') == message_id:
                # Update the message's information
                self.data['messages'][i].update(updated_data)
                self.data['messages'][i]['updated_at'] = datetime.now().isoformat()
                
                # Save changes to file
                if self._save_data():
                    return self.data['messages'][i]
                else:
                    # If save failed, revert the changes
                    self.data['messages'][i] = message
                    return None
        return None
    
    def delete_message(self, message_id: int) -> bool:
        """
        Remove a message from the system.
        
        This is like removing a letter from our message filing system.
        
        Args:
            message_id: The ID of the message to remove
            
        Returns:
            True if message was deleted successfully, False if message not found
        """
        # Find and remove the message
        for i, message in enumerate(self.data['messages']):
            if message.get('id') == message_id:
                del self.data['messages'][i]
                # Save changes to file
                return self._save_data()
        return False
    
    # ========================================
    # INQUIRY MANAGEMENT FUNCTIONS
    # ========================================
    
    def create_inquiry(self, inquiry_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a new inquiry to our system.
        
        This is like adding a new question or request to our inquiry filing system.
        
        Args:
            inquiry_data: Dictionary containing inquiry information (student, faculty, subject, etc.)
            
        Returns:
            The created inquiry data with assigned ID, or None if creation failed
        """
        # Generate a new unique ID for this inquiry
        max_id = max([inq.get('id', 0) for inq in self.data['inquiries']], default=0)
        inquiry_data['id'] = max_id + 1
        
        # Add current timestamp for when this inquiry was created
        inquiry_data['created_at'] = datetime.now().isoformat()
        inquiry_data['updated_at'] = datetime.now().isoformat()
        
        # Add the new inquiry to our list
        self.data['inquiries'].append(inquiry_data)
        
        # Save the changes to file
        if self._save_data():
            return inquiry_data
        else:
            # If save failed, remove the inquiry from memory
            self.data['inquiries'].remove(inquiry_data)
            return None
    
    def get_inquiry(self, inquiry_id: int) -> Optional[Dict[str, Any]]:
        """
        Find and retrieve a specific inquiry.
        
        This is like looking up a specific question in our inquiry filing system.
        
        Args:
            inquiry_id: The unique ID of the inquiry to find
            
        Returns:
            The inquiry information if found, None if not found
        """
        # Look through all inquiries to find one with matching ID
        for inquiry in self.data['inquiries']:
            if inquiry.get('id') == inquiry_id:
                return inquiry
        return None
    
    def get_inquiries_by_student(self, student_id: int) -> List[Dict[str, Any]]:
        """
        Get all inquiries made by a specific student.
        
        This is like getting all questions asked by a specific student.
        
        Args:
            student_id: The ID of the student whose inquiries we want
            
        Returns:
            List of all inquiries made by this student
        """
        student_inquiries = []
        # Look through all inquiries to find ones made by this student
        for inquiry in self.data['inquiries']:
            if inquiry.get('student_id') == student_id:
                student_inquiries.append(inquiry)
        return student_inquiries
    
    def get_inquiries_by_faculty(self, faculty_id: int) -> List[Dict[str, Any]]:
        """
        Get all inquiries assigned to a specific faculty member.
        
        This is like getting all questions that need to be answered by a specific faculty member.
        
        Args:
            faculty_id: The ID of the faculty member whose inquiries we want
            
        Returns:
            List of all inquiries assigned to this faculty member
        """
        faculty_inquiries = []
        # Look through all inquiries to find ones assigned to this faculty member
        for inquiry in self.data['inquiries']:
            if inquiry.get('faculty_id') == faculty_id:
                faculty_inquiries.append(inquiry)
        return faculty_inquiries
    
    def update_inquiry(self, inquiry_id: int, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing inquiry.
        
        This is like updating a question with new information (like adding an answer).
        
        Args:
            inquiry_id: The ID of the inquiry to update
            updated_data: New information to replace the old information
            
        Returns:
            The updated inquiry data if successful, None if inquiry not found
        """
        # Find the inquiry in our list
        for i, inquiry in enumerate(self.data['inquiries']):
            if inquiry.get('id') == inquiry_id:
                # Update the inquiry's information
                self.data['inquiries'][i].update(updated_data)
                self.data['inquiries'][i]['updated_at'] = datetime.now().isoformat()
                
                # Save changes to file
                if self._save_data():
                    return self.data['inquiries'][i]
                else:
                    # If save failed, revert the changes
                    self.data['inquiries'][i] = inquiry
                    return None
        return None
    
    def delete_inquiry(self, inquiry_id: int) -> bool:
        """
        Remove an inquiry from the system.
        
        This is like removing a question from our inquiry filing system.
        
        Args:
            inquiry_id: The ID of the inquiry to remove
            
        Returns:
            True if inquiry was deleted successfully, False if inquiry not found
        """
        # Find and remove the inquiry
        for i, inquiry in enumerate(self.data['inquiries']):
            if inquiry.get('id') == inquiry_id:
                del self.data['inquiries'][i]
                # Save changes to file
                return self._save_data()
        return False
    
    # ========================================
    # CONVERSATION MANAGEMENT FUNCTIONS
    # ========================================
    
    def create_conversation(self, conversation_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a new conversation to our system.
        
        Args:
            conversation_data: Dictionary containing conversation information (participants, is_group, etc.)
            
        Returns:
            The created conversation data with assigned ID, or None if creation failed
        """
        # Generate a new unique ID for this conversation
        max_id = max([conv.get('id', 0) for conv in self.data['conversations']], default=0)
        conversation_data['id'] = max_id + 1
        
        # Add current timestamp for when this conversation was created
        conversation_data['created_at'] = self._get_current_timestamp()
        conversation_data['updated_at'] = self._get_current_timestamp()
        
        # Add the new conversation to our list
        self.data['conversations'].append(conversation_data)
        
        # Save the changes to file
        if self._save_data():
            return conversation_data
        else:
            # If save failed, remove the conversation from memory
            self.data['conversations'].remove(conversation_data)
            return None
    
    def get_conversation(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """
        Find and retrieve a specific conversation.
        
        Args:
            conversation_id: The unique ID of the conversation to find
            
        Returns:
            The conversation information if found, None if not found
        """
        for conversation in self.data['conversations']:
            if conversation.get('id') == conversation_id:
                return conversation
        return None
    
    def get_conversations_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all conversations involving a specific user.
        
        Args:
            user_id: The ID of the user whose conversations we want
            
        Returns:
            List of all conversations involving this user
        """
        user_conversations = []
        for conversation in self.data['conversations']:
            if user_id in conversation.get('participants', []):
                user_conversations.append(conversation)
        return user_conversations
    
    def _get_current_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.
        
        Returns:
            Current timestamp as ISO string
        """
        return datetime.now().isoformat()
    
    # ========================================
    # NOTIFICATION MANAGEMENT FUNCTIONS
    # ========================================
    
    def create_notification(self, notification_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a new notification to our system.
        
        This is like adding a new alert or reminder to our notification system.
        
        Args:
            notification_data: Dictionary containing notification information (user, title, message, etc.)
            
        Returns:
            The created notification data with assigned ID, or None if creation failed
        """
        # Generate a new unique ID for this notification
        max_id = max([notif.get('id', 0) for notif in self.data['notifications']], default=0)
        notification_data['id'] = max_id + 1
        
        # Add current timestamp for when this notification was created
        notification_data['created_at'] = datetime.now().isoformat()
        
        # Add the new notification to our list
        self.data['notifications'].append(notification_data)
        
        # Save the changes to file
        if self._save_data():
            return notification_data
        else:
            # If save failed, remove the notification from memory
            self.data['notifications'].remove(notification_data)
            return None
    
    def get_notifications_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all notifications for a specific user.
        
        This is like getting all alerts and reminders for a specific person.
        
        Args:
            user_id: The ID of the user whose notifications we want
            
        Returns:
            List of all notifications for this user
        """
        user_notifications = []
        # Look through all notifications to find ones for this user
        for notification in self.data['notifications']:
            if notification.get('user_id') == user_id:
                user_notifications.append(notification)
        return user_notifications
    
    def mark_notification_as_read(self, notification_id: int) -> bool:
        """
        Mark a notification as read.
        
        This is like checking off a reminder that you've seen.
        
        Args:
            notification_id: The ID of the notification to mark as read
            
        Returns:
            True if notification was updated successfully, False if not found
        """
        # Find the notification and mark it as read
        for i, notification in enumerate(self.data['notifications']):
            if notification.get('id') == notification_id:
                self.data['notifications'][i]['is_read'] = True
                # Save changes to file
                return self._save_data()
        return False
    
    # ========================================
    # SEARCH AND FILTER FUNCTIONS
    # ========================================
    
    def search_messages(self, search_term: str, user_id: int = None) -> List[Dict[str, Any]]:
        """
        Search for messages containing specific text.
        
        This is like using a search function to find letters containing certain words.
        
        Args:
            search_term: The text to search for in message content and subject
            user_id: Optional user ID to limit search to messages involving this user
            
        Returns:
            List of messages that match the search term
        """
        matching_messages = []
        search_term_lower = search_term.lower()
        
        # Look through all messages to find ones containing the search term
        for message in self.data['messages']:
            # If user_id is specified, only search messages involving this user
            if user_id and (message.get('sender_id') != user_id and message.get('receiver_id') != user_id):
                continue
                
            # Check if search term is in subject or content
            subject = message.get('subject', '').lower()
            content = message.get('content', '').lower()
            
            if search_term_lower in subject or search_term_lower in content:
                matching_messages.append(message)
        
        return matching_messages
    
    def filter_messages_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get all messages with a specific status.
        
        This is like filtering letters by their status (pending, sent, resolved).
        
        Args:
            status: The status to filter by (pending, sent, resolved, etc.)
            
        Returns:
            List of messages with the specified status
        """
        filtered_messages = []
        # Look through all messages to find ones with matching status
        for message in self.data['messages']:
            if message.get('status') == status:
                filtered_messages.append(message)
        return filtered_messages
    
    def filter_messages_by_priority(self, priority: str) -> List[Dict[str, Any]]:
        """
        Get all messages with a specific priority level.
        
        This is like filtering letters by their priority (normal, high, urgent).
        
        Args:
            priority: The priority to filter by (normal, high, urgent)
            
        Returns:
            List of messages with the specified priority
        """
        filtered_messages = []
        # Look through all messages to find ones with matching priority
        for message in self.data['messages']:
            if message.get('priority') == priority:
                filtered_messages.append(message)
        return filtered_messages
    
    def filter_messages_by_type(self, message_type: str) -> List[Dict[str, Any]]:
        """
        Get all messages of a specific type.
        
        This is like filtering letters by their type (academic, administrative, technical, general).
        
        Args:
            message_type: The type to filter by (academic, administrative, technical, general)
            
        Returns:
            List of messages with the specified type
        """
        filtered_messages = []
        # Look through all messages to find ones with matching type
        for message in self.data['messages']:
            if message.get('message_type') == message_type:
                filtered_messages.append(message)
        return filtered_messages
    
    # ========================================
    # STATISTICS AND ANALYTICS FUNCTIONS
    # ========================================
    
    def get_user_message_count(self, user_id: int) -> Dict[str, int]:
        """
        Get message statistics for a specific user.
        
        This is like getting a summary of how many messages a person has sent and received.
        
        Args:
            user_id: The ID of the user to get statistics for
            
        Returns:
            Dictionary with counts of sent, received, and total messages
        """
        sent_count = 0
        received_count = 0
        
        # Count messages sent and received by this user
        for message in self.data['messages']:
            if message.get('sender_id') == user_id:
                sent_count += 1
            if message.get('receiver_id') == user_id:
                received_count += 1
        
        return {
            'sent': sent_count,
            'received': received_count,
            'total': sent_count + received_count
        }
    
    def get_unread_message_count(self, user_id: int) -> int:
        """
        Get the number of unread messages for a specific user.
        
        This is like counting how many unopened letters a person has.
        
        Args:
            user_id: The ID of the user to count unread messages for
            
        Returns:
            Number of unread messages for this user
        """
        unread_count = 0
        
        # Count unread messages received by this user
        for message in self.data['messages']:
            if (message.get('receiver_id') == user_id and 
                not message.get('is_read', False)):
                unread_count += 1
        
        return unread_count
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """
        Get overall system statistics.
        
        This is like getting a summary of all activity in our messaging system.
        
        Returns:
            Dictionary with various system statistics
        """
        return {
            'total_users': len(self.data['users']),
            'total_messages': len(self.data['messages']),
            'total_inquiries': len(self.data['inquiries']),
            'total_notifications': len(self.data['notifications']),
            'total_conversations': len(self.data['conversations']),
            'pending_messages': len(self.filter_messages_by_status('pending')),
            'unread_messages': sum(1 for msg in self.data['messages'] if not msg.get('is_read', False)),
            'resolved_inquiries': len([inq for inq in self.data['inquiries'] if inq.get('status') == 'resolved'])
        }
        
    def reload_data(self) -> dict:
        """Reload JSON from disk into memory for realtime updates."""
        self.data = self._load_data()
        return self.data


# ========================================
# EXAMPLE USAGE AND TESTING
# ========================================


def example_usage():
    """
    Example of how to use the DataManager class.
    
    This shows how to use our data manager like a real application would.
    """
    # Create a new data manager instance
    # This is like hiring our smart assistant to manage our filing system
    dm = DataManager()
    
    # Example: Create a new user
    # This is like adding a new person to our system
    new_user = {
        'name': 'John Doe',
        'email': 'john.doe@student.cmu.edu.ph',
        'role': 'student',
        'department': 'Computer Science',
        'year_level': '2nd Year',
        'status': 'online'
    }
    created_user = dm.create_user(new_user)
    print(f"Created user: {created_user}")
    
    # Example: Get all users
    # This is like getting a list of everyone in our system
    all_users = dm.get_all_users()
    print(f"Total users: {len(all_users)}")
    
    # Example: Create a new message
    # This is like sending a letter to someone
    new_message = {
        'sender_id': 1,
        'receiver_id': 2,
        'subject': 'Hello from DataManager',
        'content': 'This is a test message created using our data manager!',
        'message_type': 'general',
        'priority': 'normal',
        'status': 'sent',
        'is_read': False
    }
    created_message = dm.create_message(new_message)
    print(f"Created message: {created_message}")
    
    # Example: Search for messages
    # This is like searching for letters containing certain words
    search_results = dm.search_messages('test')
    print(f"Found {len(search_results)} messages containing 'test'")
    
    # Example: Get system statistics
    # This is like getting a summary of our entire system
    stats = dm.get_system_statistics()
    print(f"System statistics: {stats}")


if __name__ == "__main__":
    # Run the example when this file is executed directly
    example_usage()
