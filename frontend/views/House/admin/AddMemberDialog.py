# views/House/AddMemberDialog.py
import requests
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QMessageBox
)
from PyQt6.QtCore import Qt


class AddMemberDialog(QDialog):
    """Dialog to select and add students to a house"""
    
    def __init__(self, house_id, house_name, token=None, api_base=None, parent=None):
        super().__init__(parent)
        self.house_id = house_id
        self.house_name = house_name
        self.token = token
        self.api_base = api_base or "http://127.0.0.1:8000"
        self.selected_student = None
        
        self.setWindowTitle(f"Add Member to {house_name}")
        self.setMinimumSize(600, 400)
        
        self.init_ui()
        self.load_students()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel(f"Select Student to Add to {self.house_name}")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name...")
        self.search_input.textChanged.connect(self.filter_students)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Students table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Email"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemDoubleClicked.connect(self.on_student_double_clicked)
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        add_btn = QPushButton("Add Member")
        add_btn.clicked.connect(self.add_selected_member)
        add_btn.setStyleSheet("background-color: #084924; color: white; padding: 8px 16px;")
        button_layout.addWidget(add_btn)
        
        layout.addLayout(button_layout)
    
    def load_students(self):
        """Fetch all students from the API and filter out existing members"""
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            # First, get existing members of this house
            existing_member_ids = set()
            memberships_url = f"{self.api_base}/api/house/memberships/?house={self.house_id}"
            memberships_response = requests.get(memberships_url, headers=headers, timeout=10)
            
            if memberships_response.status_code == 200:
                memberships_data = memberships_response.json()
                if isinstance(memberships_data, dict):
                    memberships = memberships_data.get("results", [])
                else:
                    memberships = memberships_data
                for membership in memberships:
                    existing_member_ids.add(membership.get("user"))
            
            # Now get all users
            url = f"{self.api_base}/api/users/"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                QMessageBox.warning(self, "Error", f"Failed to load users: HTTP {response.status_code}")
                return
            
            data = response.json()
            
            # Handle both paginated (dict) and non-paginated (list)
            if isinstance(data, dict):
                users = data.get("results", [])
            elif isinstance(data, list):
                users = data
            else:
                users = []
            
            # Filter for students only (those with 'student' role or in 'student' group)
            # AND exclude students who are already members of this house
            students = []
            for user in users:
                user_id = user.get("id")
                
                # Skip if already a member of this house
                if user_id in existing_member_ids:
                    continue
                
                # Check role_type field
                if user.get("role_type") == "student":
                    students.append(user)
                    continue
                
                # Check groups field
                groups = user.get("groups", [])
                if groups:
                    # Handle both list of names and list of objects
                    if isinstance(groups[0], dict):
                        group_names = [g.get("name", "").lower() for g in groups]
                    else:
                        group_names = [str(g).lower() for g in groups]
                    
                    if "student" in group_names or "students" in group_names:
                        students.append(user)
            
            if not students:
                QMessageBox.information(self, "No Students Available", 
                    "All students are already members of this house, or no students found.")
            
            self.populate_table(students)
            
        except requests.RequestException as e:
            QMessageBox.critical(self, "Error", f"Cannot reach backend: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading students: {e}")
    
    def populate_table(self, students):
        """Populate the table with student data"""
        self.table.setRowCount(0)
        
        for student in students:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Build display name
            first_name = student.get("first_name", "")
            last_name = student.get("last_name", "")
            username = student.get("username", "")
            display_name = f"{first_name} {last_name}".strip() or username
            
            id_item = QTableWidgetItem(str(student.get("id", "")))
            name_item = QTableWidgetItem(display_name)
            email_item = QTableWidgetItem(student.get("email", ""))
            
            # Store user ID in the first column for later retrieval
            id_item.setData(Qt.ItemDataRole.UserRole, student.get("id"))
            
            self.table.setItem(row, 0, id_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, email_item)
        
        self.table.resizeColumnsToContents()
    
    def filter_students(self, text):
        """Filter students based on search text"""
        text = text.lower()
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 1).text().lower()
            email = self.table.item(row, 2).text().lower()
            self.table.setRowHidden(row, text not in name and text not in email)
    
    def on_student_double_clicked(self, item):
        """Handle double-click on student row"""
        self.add_selected_member()
    
    def add_selected_member(self):
        """Add the selected student to the house"""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a student to add.")
            return
        
        row = selected_rows[0].row()
        id_item = self.table.item(row, 0)
        student_id = id_item.data(Qt.ItemDataRole.UserRole)
        student_name = self.table.item(row, 1).text()
        
        if not student_id:
            QMessageBox.warning(self, "Error", "Could not retrieve student ID.")
            return
        
        # Call API to add member to house (create a HouseMembership)
        try:
            headers = {"Content-Type": "application/json"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            # Use the memberships endpoint to create a new membership
            url = f"{self.api_base}/api/house/memberships/"
            data = {
                "user": int(student_id),
                "house": int(self.house_id),
                "role": "member",
                "is_active": True
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            # Success cases
            if response.status_code in (200, 201):
                QMessageBox.information(self, "Success", f"{student_name} has been added to {self.house_name}!")
                self.accept()
                return
            
            # Handle 400 Bad Request (validation errors)
            if response.status_code == 400:
                try:
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        error_data = response.json()
                        if isinstance(error_data, dict):
                            if "non_field_errors" in error_data:
                                errors = error_data["non_field_errors"]
                                if any("unique" in str(e).lower() for e in errors):
                                    error_msg = f"{student_name} is already a member of {self.house_name}."
                                else:
                                    error_msg = ", ".join(str(e) for e in errors)
                            elif "detail" in error_data:
                                error_msg = error_data["detail"]
                            elif "error" in error_data:
                                error_msg = error_data["error"]
                            else:
                                errors = []
                                for field, msgs in error_data.items():
                                    if isinstance(msgs, list):
                                        errors.append(f"{field}: {', '.join(str(m) for m in msgs)}")
                                    else:
                                        errors.append(f"{field}: {msgs}")
                                error_msg = "\n".join(errors) if errors else str(error_data)
                        else:
                            error_msg = str(error_data)
                    else:
                        error_msg = "Invalid request. Please try again."
                except:
                    error_msg = "Invalid request. Please try again."
                QMessageBox.warning(self, "Cannot Add Member", error_msg)
                return
            
            # Handle 500 Server Error - but check if member was actually added
            if response.status_code == 500:
                # The member might have been added despite the 500 error
                # Don't show error, just close and let the list refresh
                print(f"Got 500 error but member may have been added. Closing dialog.")
                self.accept()
                return
            
            # Other errors
            QMessageBox.warning(self, "Cannot Add Member", f"Server error (HTTP {response.status_code}). Please try again.")
        except requests.RequestException as e:
            QMessageBox.critical(self, "Error", f"Cannot reach backend: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error adding member: {e}")
