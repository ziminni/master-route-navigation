import json
import os

class JSONCRUD:
    def __init__(self, filename='data.json'):
        self.filename = filename
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Ensure the JSON file exists with empty list if not present"""
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                json.dump([], f)
    
    def _read_data(self):
        """Read all data from JSON file"""
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _write_data(self, data):
        """Write data to JSON file"""
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=4)
    
    # CREATE
    def create(self, item):
        """Add a new item to the JSON file"""
        data = self._read_data()
        
        # Generate ID if not provided
        if 'id' not in item:
            item['id'] = len(data) + 1
        
        data.append(item)
        self._write_data(data)
        return item
    
    # READ
    def read_all(self):
        """Read all items from JSON file"""
        return self._read_data()
    
    def read_by_id(self, item_id):
        """Read a specific item by ID"""
        data = self._read_data()
        for item in data:
            if item.get('id') == item_id:
                return item
        return None
    
    def read_by_field(self, field, value):
        """Read items by field value"""
        data = self._read_data()
        return [item for item in data if item.get(field) == value]
    
    # UPDATE
    def update(self, item_id, updated_data):
        """Update an existing item"""
        data = self._read_data()
        
        for i, item in enumerate(data):
            if item.get('id') == item_id:
                # Update the item while preserving the ID
                updated_data['id'] = item_id
                data[i] = updated_data
                self._write_data(data)
                return updated_data
        
        return None  # Item not found
    
    # DELETE
    def delete(self, item_id):
        """Delete an item by ID"""
        data = self._read_data()
        
        for i, item in enumerate(data):
            if item.get('id') == item_id:
                deleted_item = data.pop(i)
                self._write_data(data)
                return deleted_item
        
        return None  # Item not found
    
    def delete_all(self):
        """Delete all items"""
        self._write_data([])
        return True


# # Initialize the CRUD handler
# db = JSONCRUD('users.json')

# # CREATE - Add new users
# user1 = db.create({"name": "John Doe", "email": "john@example.com", "age": 30})
# user2 = db.create({"name": "Jane Smith", "email": "jane@example.com", "age": 25})

# # READ - Get all users
# all_users = db.read_all()
# print("All users:", all_users)

# # READ - Get user by ID
# user = db.read_by_id(1)
# print("User with ID 1:", user)

# # READ - Get users by field
# johns = db.read_by_field("name", "John Doe")
# print("Users named John Doe:", johns)

# # UPDATE - Update user
# updated_user = db.update(1, {"name": "John Updated", "email": "john.updated@example.com", "age": 31})
# print("Updated user:", updated_user)

# # DELETE - Delete user
# deleted_user = db.delete(2)
# print("Deleted user:", deleted_user)

# # Final state
# final_users = db.read_all()
# print("Final users:", final_users)