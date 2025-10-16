import json
import os

class JSONCRUD:
    def __init__(self, file_path):
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create an empty JSON file if it doesn't exist."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        abs_path = os.path.join(base_dir, os.path.basename(self.file_path))
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        if not os.path.exists(abs_path):
            with open(abs_path, 'w') as f:
                json.dump([], f)
        self.file_path = abs_path

    def _read_data(self):
        """Read data from the JSON file."""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_data(self, data):
        """Write data to the JSON file."""
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def create(self, item):
        """Add a new item to the JSON file."""
        data = self._read_data()
        item["id"] = len(data) + 1
        data.append(item)
        self._write_data(data)
        return item

    def read_all(self):
        """Return all records from the JSON file."""
        return self._read_data()

    def read_by_field(self, field, value):
        """Return records where the specified field matches the value."""
        return [item for item in self._read_data() if item.get(field) == value]

    def update(self, id, updates):
        """Update an item by ID."""
        data = self._read_data()
        for item in data:
            if item["id"] == id:
                item.update(updates)
                self._write_data(data)
                return item
        return None
    def delete(self, item_id):
        # Read the data, assuming it's a list of dictionaries.
        data = self._read_data()
        
        original_length = len(data)
        
        # Create a new list with all items *except* the one to be deleted.
        data = [block for block in data if block.get("schedule_block_entry_id") != item_id]
        
        # Check if the list size changed to see if an item was deleted.
        if len(data) < original_length:
            # Assuming you have a method to write the data back.
            self._write_data(data)
            return True
        return False  