# frontend/views/Progress/Admin/studentslist.py
import threading
import traceback
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from .studentprofile import StudentProfileWidget


class StudentsListWidget(QWidget):
    def __init__(self, section_name, admin_name=None, go_back_callback=None, parent_stack=None, token=None, api_base="http://127.0.0.1:8000"):
        super().__init__()
        self.section_name = section_name
        self.admin_name = admin_name
        self.go_back_callback = go_back_callback
        self.parent_stack = parent_stack
        self.students_data = []
        self.token = token or ""
        self.api_base = (api_base or "http://127.0.0.1:8000").rstrip("/")

        self.setObjectName("studentsListWidget")
        self.init_ui()
        self.load_students()

        self.table.cellClicked.connect(self.on_cell_clicked)

    def _headers(self):
        token = (self.token or "").strip()
        if not token:
            return {}
        if token.startswith("Bearer ") or token.startswith("Token "):
            token = token.split(" ", 1)[1]
        return {"Authorization": f"Bearer {token}"}

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 20, 50, 20)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        title = QLabel(f"Students in {self.section_name}")
        title.setFont(QFont("Poppins", 14, 75))
        title.setStyleSheet(";")
        header_layout.addWidget(title)
        header_layout.addStretch()

        back_button = QPushButton("← Go Back")
        back_button.setObjectName("goBackButton")
        back_button.setFixedSize(120, 32)
        back_button.clicked.connect(self.handle_back)
        header_layout.addWidget(back_button)
        layout.addLayout(header_layout)

        self.table = QTableWidget()
        self.table.setObjectName("gradesTable")
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "No.", "Student ID", "Name", "Grade", "Remarks", "GWA", "Missing Requirement"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setWordWrap(True)

        widths = [60, 130, 0, 80, 100, 80, 0]
        header = self.table.horizontalHeader()
        for i, w in enumerate(widths):
            if w == 0:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                self.table.setColumnWidth(i, w)

        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_students(self):
        url = f"{self.api_base}/api/progress/admin/section/{self.section_name}/students/"

        def fetch():
            try:
                print(f"DEBUG: Loading students from {url}")
                r = requests.get(url, headers=self._headers(), timeout=10)
                print(f"DEBUG: Response status: {r.status_code}")
                
                if r.status_code == 200:
                    data = r.json()
                    print(f"DEBUG: Received data type: {type(data)}")
                    
                    # The backend returns {"students": [...]}
                    if isinstance(data, dict):
                        if "students" in data:
                            self.students_data = data.get("students", [])
                            print(f"DEBUG: Loaded {len(self.students_data)} students")
                        elif "detail" in data:
                            print(f"DEBUG: Error from API: {data['detail']}")
                            self.students_data = []
                        else:
                            # Assume the dict itself contains the list
                            self.students_data = data
                    elif isinstance(data, list):
                        self.students_data = data
                    else:
                        print(f"DEBUG: Unexpected response format")
                        self.students_data = []
                else:
                    print(f"❌ API error {r.status_code}: {r.text}")
                    self.students_data = []
            except Exception as e:
                print(f"❌ Exception fetching students: {e}")
                traceback.print_exc()
                self.students_data = []
            
            # Update UI on main thread
            self.populate()

        threading.Thread(target=fetch, daemon=True).start()

    def populate(self):
        self.table.setRowCount(0)
        
        if not self.students_data:
            # Show empty message
            self.table.setRowCount(1)
            self.table.setSpan(0, 0, 1, 7)
            empty_item = QTableWidgetItem("No students found in this section")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_item.setForeground(QColor("#6c757d"))
            self.table.setItem(0, 0, empty_item)
            return

        print(f"DEBUG: Populating table with {len(self.students_data)} students")
        for i, student in enumerate(self.students_data, start=1):
            self.table.insertRow(self.table.rowCount())
            
            # Extract data with fallbacks
            student_id = student.get("student_id") or student.get("id") or ""
            name = student.get("name") or student.get("student_name") or ""
            grade = student.get("grade", "")
            remarks = student.get("remarks", "")
            gwa = student.get("gwa", "")
            missing_req = student.get("missing_requirement", "")
            
            values = [
                str(i),
                student_id,
                name,
                str(grade),
                str(remarks),
                str(gwa),
                str(missing_req)
            ]
            
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Clickable visual for student id/name
                if col in [1, 2]:
                    item.setForeground(QColor("#155724"))
                    font = item.font()
                    font.setUnderline(True)
                    item.setFont(font)
                    item.setToolTip("Click to open profile")

                # Mark failed remarks in red
                if col == 4 and str(val).strip().upper() == "FAILED":
                    item.setForeground(QColor("#ff0000"))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    
                # Highlight low grades
                if col == 3:
                    try:
                        grade_val = float(val)
                        if grade_val > 3.0:
                            item.setForeground(QColor("#ff0000"))
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)
                    except ValueError:
                        pass

                self.table.setItem(i - 1, col, item)

        self.table.resizeRowsToContents()

    def on_cell_clicked(self, row, column):
        # Only open profile when clicking student id (col 1) or name (col 2)
        if column not in [1, 2]:
            return

        # Check if we're showing the "no students" message
        if self.table.rowCount() == 1 and self.table.item(0, 0) and "No students" in self.table.item(0, 0).text():
            return

        try:
            student = self.students_data[row]
        except (IndexError, KeyError) as e:
            print(f"❌ Error accessing student data: {e}")
            QMessageBox.warning(self, "Error", "Could not access student data.")
            return

        # Get student ID
        student_id = student.get("student_id") or student.get("id") or ""
        
        if not student_id:
            print("❌ No student ID found")
            QMessageBox.warning(self, "Error", "No student ID available for this student.")
            return

        print(f"DEBUG: Opening profile for student ID: {student_id}")
        profile_page = StudentProfileWidget(
            student_id=student_id,
            admin_name=self.admin_name,
            go_back_callback=self.show_self,
            token=self.token,
            api_base=self.api_base
        )

        if self.parent_stack:
            self.parent_stack.addWidget(profile_page)
            self.parent_stack.setCurrentWidget(profile_page)

    def show_self(self):
        if self.parent_stack:
            self.parent_stack.setCurrentWidget(self)

    def handle_back(self):
        if callable(self.go_back_callback):
            self.go_back_callback()