import sys
import random
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QCheckBox, QPushButton, QLabel, QFrame, QScrollArea,
                             QDateEdit, QComboBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QStyledItemDelegate,QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QPainter, QColor, QFont, QPainterPath, QFontDatabase


class StudentAvatar(QLabel):
    """Custom avatar widget with circular shape and initials"""
    
    def __init__(self, name, color, size=40):
        super().__init__()
        self.name = name
        self.color = color
        self.size = size
        self.setFixedSize(size, size)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create circular path
        path = QPainterPath()
        path.addEllipse(0, 0, self.size, self.size)
        painter.setClipPath(path)
        
        # Fill background
        painter.fillRect(self.rect(), QColor(self.color))
        
        # Draw initials
        initials = self.get_initials()
        painter.setPen(QColor("white"))
        font = QFont("Poppins", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, initials)
        
    def get_initials(self):
        """Extract initials from name"""
        parts = self.name.split()
        if len(parts) >= 2:
            return parts[0][0].upper() + parts[-1][0].upper()
        elif len(parts) == 1:
            return parts[0][:2].upper()
        return "??"


class AttendanceRow(QFrame):
    """Single student attendance row with smaller fonts"""
    
    attendance_changed = pyqtSignal(int, str, bool)
    
    def __init__(self, student_data, current_date, is_present=True):
        super().__init__()
        self.student_data = student_data
        self.current_date = current_date
        self.is_present = is_present
        
        self.setup_ui()
        self.update_display()
        
    def setup_ui(self):
        self.setFixedHeight(45)  # Reduced height
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            AttendanceRow {
                background-color: white;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)  # Reduced margins
        layout.setSpacing(8)  # Reduced spacing
        
        # Student number
        self.no_label = QLabel(str(self.student_data["no"]))
        self.no_label.setFixedWidth(30)  # Reduced width
        self.no_label.setStyleSheet("""
            font-family: 'Poppins';
            font-size: 11px;  # Smaller font
            color: #666;
            font-weight: 500;
        """)
        layout.addWidget(self.no_label)
        
        # Avatar and name
        student_info_widget = QWidget()
        student_layout = QHBoxLayout(student_info_widget)
        student_layout.setContentsMargins(0, 0, 0, 0)
        student_layout.setSpacing(6)  # Reduced spacing
        
        self.avatar = StudentAvatar(
            self.student_data["name"], 
            self.student_data["color"],
            size=28  # Smaller avatar
        )
        student_layout.addWidget(self.avatar)
        
        self.name_label = QLabel(self.student_data["name"])
        self.name_label.setStyleSheet("""
            font-family: 'Poppins';
            font-size: 11px;  # Smaller font
            color: #333;
            font-weight: 500;
        """)
        student_layout.addWidget(self.name_label)
        student_layout.addStretch()
        
        layout.addWidget(student_info_widget, 3)
        
        # Present checkbox
        self.present_check = QCheckBox("Present")
        self.present_check.setStyleSheet(self.get_present_style())
        self.present_check.stateChanged.connect(self.on_present_changed)
        layout.addWidget(self.present_check, 1)
        
        # Absent checkbox
        self.absent_check = QCheckBox("Absent")
        self.absent_check.setStyleSheet(self.get_absent_style())
        self.absent_check.stateChanged.connect(self.on_absent_changed)
        layout.addWidget(self.absent_check, 1)
        
        # Status indicator
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(10, 10)  # Smaller indicator
        self.status_indicator.setStyleSheet("border-radius: 5px;")
        layout.addWidget(self.status_indicator)
    
    def get_present_style(self):
        return """
            QCheckBox {
                font-family: 'Poppins';
                font-size: 11px;  # Smaller font
                color: #2d6a4f;
                spacing: 6px;  # Reduced spacing
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 16px;  # Smaller indicator
                height: 16px;
                border: 1px solid #2d6a4f;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #2d6a4f;
                border-color: #2d6a4f;
            }
            QCheckBox::indicator:checked:after {
                content: "✓";
                color: white;
                font-size: 12px;  # Smaller checkmark
                font-weight: bold;
            }
        """
    
    def get_absent_style(self):
        return """
            QCheckBox {
                font-family: 'Poppins';
                font-size: 11px;  # Smaller font
                color: #c9485b;
                spacing: 6px;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #c9485b;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #c9485b;
                border-color: #c9485b;
            }
            QCheckBox::indicator:checked:after {
                content: "✗";
                color: white;
                font-size: 10px;  # Smaller X
                font-weight: bold;
            }
        """
    
    def on_present_changed(self, state):
        if state == Qt.CheckState.Checked.value:
            self.absent_check.setChecked(False)
            self.is_present = True
            self.update_display()
            self.attendance_changed.emit(
                self.student_data["id"], 
                self.current_date, 
                True
            )
    
    def on_absent_changed(self, state):
        if state == Qt.CheckState.Checked.value:
            self.present_check.setChecked(False)
            self.is_present = False
            self.update_display()
            self.attendance_changed.emit(
                self.student_data["id"], 
                self.current_date, 
                False
            )
    
    def update_display(self):
        """Update visual state based on attendance"""
        if self.is_present:
            self.status_indicator.setStyleSheet("""
                background-color: #2d6a4f;
                border-radius: 6px;
            """)
        else:
            self.status_indicator.setStyleSheet("""
                background-color: #c9485b;
                border-radius: 6px;
            """)
    
    def set_attendance(self, is_present):
        """Set attendance status programmatically"""
        self.is_present = is_present
        self.present_check.setChecked(is_present)
        self.absent_check.setChecked(not is_present)
        self.update_display()
    
    def update_date(self, new_date, is_present):
        """Update for new date"""
        self.current_date = new_date
        self.set_attendance(is_present)


class TableItemDelegate(QStyledItemDelegate):
    """Custom delegate for table items with Poppins font"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.font = QFont("Poppins", 10)
        
    def paint(self, painter, option, index):
        # Set font
        painter.setFont(self.font)
        super().paint(painter, option, index)


class AttendanceTableWidget(QFrame):
    """Table widget for overview attendance - READ ONLY"""
    
    attendance_changed = pyqtSignal(int, str, bool)
    
    def __init__(self):
        super().__init__()
        self.attendance_data = {}
        self.dates = []
        self.students = []
        self.readonly = False  # Track readonly state
        self.single_student_mode = False
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.init_ui()
    
    def set_readonly(self, readonly):
        """Set the table to read-only mode"""
        self.readonly = readonly
        self.update_readonly_state()
    
    def update_readonly_state(self):
        """Update UI based on readonly state"""
        if hasattr(self, 'table'):
            # Disable editing of cells
            self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            
            # Make all cells non-editable
            for row in range(self.table.rowCount()):
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Disable checkboxes in student rows
            for row in range(1, self.table.rowCount()):  # Skip header row
                for col in range(3, self.table.columnCount()):  # Date columns
                    widget = self.table.cellWidget(row, col)
                    if widget:
                        checkbox = widget.findChild(QCheckBox)
                        if checkbox:
                            checkbox.setEnabled(not self.readonly)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create table
        self.table = QTableWidget()
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Apply consistent green styling
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                font-family: 'Poppins';
                font-size: 11px;
                gridline-color: transparent;
                selection-background-color: #e8f5e9;
            }
            QTableWidget::item {
                padding: 6px;
                font-family: 'Poppins';
                font-size: 11px;
                border-bottom: 1px solid #e0e0e0;
            }
            QHeaderView::section {
                background-color: #2d6a4f;
                color: white;
                padding: 8px;
                border: none;
                font-weight: 600;
                font-size: 11px;
                font-family: 'Poppins';
            }
            QHeaderView::section:first {
                border-top-left-radius: 0px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 0px;
            }
        """)
        
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Disable editing
        
        # Set scrolling
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        layout.addWidget(self.table)
    
    def load_data(self, students, dates):
        """Load student and date data into the table"""
        self.table.clear()
        self.attendance_data = {}
        self.students = students
        self.single_student_mode = len(students) == 1
        self.dates = dates
        
        num_students = len(students)
        num_date_columns = len(dates)
        
        # Setup table structure
        total_columns = 3 + num_date_columns
        self.table.setColumnCount(total_columns)
        self.table.setRowCount(num_students + 1)  # +1 for header row
        
        # Set headers with consistent green styling
        headers = ["No", "Student Name", "Absences"]
        for date, _ in dates:
            headers.append(f"{date}")
        
        self.table.setHorizontalHeaderLabels(headers)
        
        # Configure header
        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Set column widths
        self.table.setColumnWidth(0, 60)    # No column
        self.table.setColumnWidth(1, 200)   # Student Name
        self.table.setColumnWidth(2, 80)    # Absences
        
        # Set fixed width for date columns
        for i in range(num_date_columns):
            self.table.setColumnWidth(3 + i, 100)
        
        # Hide vertical header
        self.table.verticalHeader().setVisible(False)
        
        # Set row height for header row
        self.table.setRowHeight(0, 40)
        
        # Add header row with green background
        for col in range(total_columns):
            item = QTableWidgetItem(headers[col])
            item.setBackground(QColor("#2d6a4f"))
            item.setForeground(QColor("white"))
            item.setFont(QFont("Poppins", 11, QFont.Weight.Bold))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Not editable
            self.table.setItem(0, col, item)

            # Adjust column widths for single student
        if self.single_student_mode:
            self.table.setColumnWidth(1, 250)  # Wider name column
            # Hide "Absences" column for single student
            self.table.setColumnWidth(2, 0)
            self.table.horizontalHeader().hideSection(2)
        
        # Add all students to the table
        for idx, student in enumerate(students):
            row = idx + 1  # +1 because row 0 is header
            
            # Add student number
            num_item = QTableWidgetItem(str(student["no"]))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            num_item.setFont(QFont("Poppins", 11))
            num_item.setForeground(QColor("#666666"))
            num_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Not editable
            self.table.setItem(row, 0, num_item)
            
            # Add student name with avatar
            name_widget = self.create_student_name_widget(student)
            self.table.setCellWidget(row, 1, name_widget)
            
            # Add absences count column
            absences_item = QTableWidgetItem("0")
            absences_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            absences_item.setFont(QFont("Poppins", 11, QFont.Weight.Bold))
            absences_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Not editable
            self.table.setItem(row, 2, absences_item)
            
            # Initialize attendance data for this student
            self.attendance_data[row] = {}
        
        # Add all date columns
        for col_idx, (date, initial_mode) in enumerate(dates):
            date_col = 3 + col_idx
            
            # Add checkboxes for each student in this date column
            for student_idx in range(num_students):
                row = student_idx + 1
                checkbox_widget = self.create_checkbox_widget(row, date_col, initial_mode)
                self.table.setCellWidget(row, date_col, checkbox_widget)
                
                # Initialize attendance state
                if date_col not in self.attendance_data[row]:
                    self.attendance_data[row][date_col] = {
                        'checked': False,
                        'mode': initial_mode,
                        'date': date
                    }
        
        # Set row heights for student rows
        for i in range(1, num_students + 1):
            self.table.setRowHeight(i, 45)
        
        # Update absence counts
        self.update_absence_counts()
        
        # Apply readonly state
        self.update_readonly_state()

        
    
    def create_student_name_widget(self, student):
        """Create a widget for displaying student name with avatar"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(8)
        
        # Avatar
        avatar = StudentAvatar(student["name"], student["color"], size=28)
        layout.addWidget(avatar)
        
        # Student name label
        name_label = QLabel(student["name"])
        name_label.setStyleSheet("""
            font-family: 'Poppins';
            font-size: 11px;
            color: #333;
            font-weight: 500;
        """)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        layout.addStretch()
        
        return widget
    
    def create_checkbox_widget(self, row, col, mode):
        """Create a checkbox widget - disabled for read-only mode"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        
        checkbox = QCheckBox()
        label = QLabel(mode)
        label.setStyleSheet("font-family: 'Poppins'; font-size: 11px;")
        
        # Apply styling
        self.update_checkbox_style(checkbox, label, mode, False)
        
        # Connect checkbox - but only if not readonly
        if not self.readonly:
            checkbox.stateChanged.connect(
                lambda state, r=row, c=col, cb=checkbox, lbl=label: 
                self.on_checkbox_changed(r, c, state, cb, lbl)
            )
        else:
            checkbox.setEnabled(False)  # Disable for read-only
        
        layout.addWidget(checkbox)
        layout.addWidget(label)
        layout.addStretch()
        
        return widget
    
    def update_checkbox_style(self, checkbox, label, mode, is_checked):
        """Update checkbox and label styling"""
        if mode == "Present":
            label.setText("Present")
            if is_checked:
                checkbox.setStyleSheet("""
                    QCheckBox {
                        spacing: 6px;
                        background-color: transparent;
                    }
                    QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
                        border: 1px solid #2d6a4f;
                        border-radius: 3px;
                        background-color: white;
                    }
                    QCheckBox::indicator:checked {
                        background-color: #2d6a4f;
                        border-color: #2d6a4f;
                    }
                    QCheckBox::indicator:checked:after {
                        content: "✓";
                        color: white;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)
                label.setStyleSheet("""
                    font-family: 'Poppins';
                    font-size: 11px;
                    color: #2d6a4f;
                    font-weight: 500;
                """)
            else:
                checkbox.setStyleSheet("""
                    QCheckBox {
                        spacing: 6px;
                        background-color: transparent;
                    }
                    QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
                        border: 1px solid #2d6a4f;
                        border-radius: 3px;
                        background-color: white;
                    }
                """)
                label.setStyleSheet("""
                    font-family: 'Poppins';
                    font-size: 11px;
                    color: #999;
                    font-weight: normal;
                """)
        else:  # Absent mode
            label.setText("Absent")
            if is_checked:
                checkbox.setStyleSheet("""
                    QCheckBox {
                        spacing: 6px;
                        background-color: transparent;
                    }
                    QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
                        border: 1px solid #c9485b;
                        border-radius: 3px;
                        background-color: white;
                    }
                    QCheckBox::indicator:checked {
                        background-color: #c9485b;
                        border-color: #c9485b;
                    }
                    QCheckBox::indicator:checked:after {
                        content: "✗";
                        color: white;
                        font-size: 10px;
                        font-weight: bold;
                    }
                """)
                label.setStyleSheet("""
                    font-family: 'Poppins';
                    font-size: 11px;
                    color: #c9485b;
                    font-weight: 500;
                """)
            else:
                checkbox.setStyleSheet("""
                    QCheckBox {
                        spacing: 6px;
                        background-color: transparent;
                    }
                    QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
                        border: 1px solid #c9485b;
                        border-radius: 3px;
                        background-color: white;
                    }
                """)
                label.setStyleSheet("""
                    font-family: 'Poppins';
                    font-size: 11px;
                    color: #999;
                    font-weight: normal;
                """)
    
    def on_checkbox_changed(self, row, col, state, checkbox, label):
        """Handle checkbox state change - only if not readonly"""
        if self.readonly:
            return
            
        is_checked = state == Qt.CheckState.Checked
        mode = self.attendance_data[row][col]['mode']
        date = self.attendance_data[row][col]['date']
        
        # Update attendance data
        self.attendance_data[row][col]['checked'] = is_checked
        
        # Update visual styling
        self.update_checkbox_style(checkbox, label, mode, is_checked)
        
        # Update the absence count for this student
        self.update_absence_counts()
        
        # Emit attendance changed signal
        student_id = self.students[row-1]["id"] if row-1 < len(self.students) else row
        is_absent = (mode == "Present" and not is_checked) or (mode == "Absent" and is_checked)
        self.attendance_changed.emit(student_id, date, not is_absent)
        
    def on_mode_changed(self, col, mode_text):
        """Handle dropdown mode change for a date column"""
        new_mode = mode_text
        num_students = self.table.rowCount() - 1
        
        # Update all student rows in this date column
        for student_idx in range(num_students):
            row = student_idx + 1
            
            # Get current checkbox state
            was_checked = self.attendance_data[row][col]['checked']
            
            # Update mode in data
            self.attendance_data[row][col]['mode'] = new_mode
            
            # INVERT the checkbox state when switching modes
            new_checked_state = not was_checked
            self.attendance_data[row][col]['checked'] = new_checked_state
            
            # Update the UI checkbox and label
            cell_widget = self.table.cellWidget(row, col)
            if cell_widget:
                checkbox = cell_widget.findChild(QCheckBox)
                label = cell_widget.findChild(QLabel)
                
                if checkbox and label:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(new_checked_state)
                    checkbox.blockSignals(False)
                    
                    self.update_checkbox_style(checkbox, label, new_mode, new_checked_state)
        
        # Update absence counts after mode change
        self.update_absence_counts()
    
    def update_absence_counts(self):
        """Update the "No. of Absences" column for all students"""
        num_students = self.table.rowCount() - 1
        num_dates = self.table.columnCount() - 3
        
        for student_idx in range(num_students):
            row = student_idx + 1
            absence_count = 0
            
            # Count absences across all date columns
            for date_idx in range(num_dates):
                col = 3 + date_idx
                
                if col in self.attendance_data.get(row, {}):
                    mode = self.attendance_data[row][col]['mode']
                    is_checked = self.attendance_data[row][col]['checked']
                    
                    # Student is absent if:
                    if (mode == "Present" and not is_checked) or (mode == "Absent" and is_checked):
                        absence_count += 1
            
            # Update the absences column
            absences_item = self.table.item(row, 2)
            if absences_item:
                absences_item.setText(str(absence_count))
    
    def get_attendance_data(self):
        """Get the current attendance data"""
        result = {}
        for row, dates in self.attendance_data.items():
            result[row] = {}
            for col, data in dates.items():
                result[row][col] = data.copy()
                # Calculate if student is absent
                mode = data['mode']
                is_checked = data['checked']
                result[row][col]['is_absent'] = (
                    (mode == "Present" and not is_checked) or 
                    (mode == "Absent" and is_checked)
                )
        return result


class AttendanceWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.students = []
        self.attendance_data = {}
        self.current_date = QDate.currentDate().toString("MMMM d")
        self.mode = "mark"
        
        
        self.init_ui()
        self.load_sample_data()
    
    def init_ui(self):
        # Make widget responsive
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Use smaller base font size
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                font-family: 'Poppins';
                font-size: 11px;
            }
            QScrollArea {
                background-color: white;
                border: none;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)  # Minimal margins
        main_layout.setSpacing(4)  # Minimal spacing
        
        # Controls section - make it more compact
        controls = self.create_controls()
        main_layout.addWidget(controls)
        
        # Stacked widget area
        self.stacked_widget = QWidget()
        self.stacked_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.stacked_layout = QVBoxLayout(self.stacked_widget)
        self.stacked_layout.setContentsMargins(0, 0, 0, 0)
        self.stacked_layout.setSpacing(0)
        
        # Mark Attendance view
        self.mark_attendance_widget = QWidget()
        self.mark_attendance_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.mark_attendance_layout = QVBoxLayout(self.mark_attendance_widget)
        self.mark_attendance_layout.setContentsMargins(0, 0, 0, 0)
        self.mark_attendance_layout.setSpacing(0)
        
        table_header = self.create_table_header()
        self.mark_attendance_layout.addWidget(table_header)
        
        self.student_scroll = self.create_student_list()
        self.mark_attendance_layout.addWidget(self.student_scroll, 1)  # Add stretch
        
        # Overview view - make it read-only
        self.overview_widget = AttendanceTableWidget()
        self.overview_widget.attendance_changed.connect(self.on_attendance_changed)
        self.overview_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.overview_widget.set_readonly(True)  # Make overview read-only
        
        # Add both views to stacked layout
        self.stacked_layout.addWidget(self.mark_attendance_widget)
        self.stacked_layout.addWidget(self.overview_widget)
        
        main_layout.addWidget(self.stacked_widget, 1)  # Add stretch factor
        
        # Footer - make it more compact
        footer = self.create_footer()
        main_layout.addWidget(footer)
        
        # Show mark attendance view by default
        self.show_mark_attendance_view()

    
    def create_controls(self):
        controls = QFrame()
        controls.setFixedHeight(60)
        controls.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #e0e0e0;
            }
            QLabel {
                font-family: 'Poppins';
                font-size: 11px;
                font-weight: 600;
                color: #333;
            }
            QDateEdit {
                font-family: 'Poppins';
                padding: 4px 8px;
                border: 1px solid #2d6a4f;
                border-radius: 4px;
                background-color: white;
                font-size: 11px;
                font-weight: 500;
                min-width: 120px;
            }
            QPushButton {
                font-family: 'Poppins';
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 11px;
                border: none;
                min-height: 28px;
            }
            QComboBox {
                font-family: 'Poppins';
                padding: 4px 8px;
                border: 1px solid #2d6a4f;
                border-radius: 4px;
                background-color: white;
                font-size: 11px;
                font-weight: 500;
                min-width: 120px;
            }
        """)
        
        layout = QHBoxLayout(controls)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # View mode selection
        view_label = QLabel("View:")
        layout.addWidget(view_label)
        
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Mark Attendance", "Overview"])
        self.view_combo.currentTextChanged.connect(self.on_view_mode_changed)
        layout.addWidget(self.view_combo)
        
        # Date selection - only show for Mark Attendance mode
        date_label = QLabel("Date:")
        layout.addWidget(date_label)
        
        self.date_picker = QDateEdit()
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
        self.date_picker.dateChanged.connect(self.on_date_changed)
        layout.addWidget(self.date_picker)
        
        layout.addStretch()
        
        # Action buttons - only show for Mark Attendance mode
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)
        
        self.mark_all_present_btn = QPushButton("Mark All Present")
        self.mark_all_present_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d6a4f;
                color: white;
            }
            QPushButton:hover {
                background-color: #245b41;
            }
        """)
        self.mark_all_present_btn.clicked.connect(self.mark_all_present)
        btn_layout.addWidget(self.mark_all_present_btn)
        
        self.mark_all_absent_btn = QPushButton("Mark All Absent")
        self.mark_all_absent_btn.setStyleSheet("""
            QPushButton {
                background-color: #c9485b;
                color: white;
            }
            QPushButton:hover {
                background-color: #b13d4f;
            }
        """)
        self.mark_all_absent_btn.clicked.connect(self.mark_all_absent)
        btn_layout.addWidget(self.mark_all_absent_btn)
        
        layout.addLayout(btn_layout)
        
        return controls
    
    def create_table_header(self):
        """Create header with consistent green styling"""
        header = QFrame()
        header.setFixedHeight(35)
        header.setStyleSheet("""
            QFrame {
                background-color: #2d6a4f;
                border: none;
                border-radius: 0px;
            }
            QLabel {
                font-family: 'Poppins';
                color: white;
                font-weight: 600;
                font-size: 11px;
                padding: 0px;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 8, 12, 8)  # Consistent padding
        layout.setSpacing(0)
        
        # Create labels with consistent styling
        no_label = QLabel("#")
        no_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(no_label, 1)
        
        name_label = QLabel("STUDENT NAME")
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(name_label, 4)
        
        present_label = QLabel("PRESENT")
        present_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(present_label, 1)
        
        absent_label = QLabel("ABSENT")
        absent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(absent_label, 1)
        
        status_label = QLabel("")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label, 1)
        
        return header
    
    def on_view_mode_changed(self, mode_text):
        """Handle view mode change with appropriate controls"""
        if mode_text == "Mark Attendance":
            self.show_mark_attendance_view()
            self.mode = "mark"
            # Show date picker and buttons
            self.date_picker.show()
            self.mark_all_present_btn.show()
            self.mark_all_absent_btn.show()
        else:  # "Overview"
            self.show_overview_view()
            self.mode = "overview"
            # Hide editing controls for overview
            self.date_picker.hide()
            self.mark_all_present_btn.hide()
            self.mark_all_absent_btn.hide()
        
        # Update statistics based on current view
        self.update_statistics()
    
    def create_student_list(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { 
                background-color: white; 
                border: none;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
        """)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.list_widget = QWidget()
        self.list_widget.setStyleSheet("background-color: white;")
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(0)
        
        scroll.setWidget(self.list_widget)
        return scroll
    
    def create_footer(self):
        """Create footer - save button hidden by default for students"""
        footer = QFrame()
        footer.setFixedHeight(40)
        footer.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid #e0e0e0;
            }
            QLabel {
                font-family: 'Poppins';
                font-size: 11px;
                color: #666;
                font-weight: 500;
            }
            QPushButton {
                font-family: 'Poppins';
                background-color: #1e5a3a;
                color: white;
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: 600;
                border: none;
                font-size: 11px;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: #16462d;
            }
        """)
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(8, 4, 8, 4)
        
        self.stats_label = QLabel("Loading attendance data...")
        self.stats_label.setMinimumWidth(300)
        layout.addWidget(self.stats_label)
        
        layout.addStretch()
        
        self.save_btn = QPushButton("Save Attendance")
        self.save_btn.clicked.connect(self.save_attendance)
        self.save_btn.hide()  # Hidden by default, shown for teachers
        layout.addWidget(self.save_btn)
        
        return footer
    
    def load_sample_data(self):
        """Load sample student data"""
        colors = ["#4db8a0", "#6b9bd1", "#f4a261", "#e76f51", "#8e7cc3", 
                 "#5da271", "#d4a574", "#c44569", "#778beb", "#cf6a87"]
        
        sample_names = [
            "Castro, Carlos Fidel", "Dela Cruz, Maria Santos", "Reyes, Juan Pablo",
            "Santos, Ana Marie", "Garcia, Jose Miguel", "Tan, Michael Johnson",
            "Lim, Samantha Rose", "Nguyen, Andrew Kim", "Smith, Jennifer Lynn",
            "Johnson, Robert James"
        ]
        
        self.students = []
        for i, name in enumerate(sample_names, 1):
            self.students.append({
                "id": i,
                "no": i,
                "name": name,
                "color": colors[i % len(colors)]
            })
        
        # Initialize attendance data structure
        self.initialize_attendance_data()
        self.populate_student_list()
        self.populate_overview_view()
    
    def initialize_attendance_data(self):
        """Initialize attendance data structure"""
        # Generate sample dates for overview view
        current_date = QDate.currentDate()
        sample_dates = []
        for i in range(-7, 8):  # 15 days around current date
            date = current_date.addDays(i)
            if date.dayOfWeek() < 6:  # Monday to Friday
                sample_dates.append((date.toString("MMMM d"), "Present"))
        
        self.sample_dates = sample_dates
        
        current_date_str = self.current_date
        
        for student in self.students:
            student_id = student["id"]
            if student_id not in self.attendance_data:
                self.attendance_data[student_id] = {}
            
            # Initialize current date with random attendance for demo
            if current_date_str not in self.attendance_data[student_id]:
                self.attendance_data[student_id][current_date_str] = random.choice([True, False])
            
            # Initialize sample dates with random attendance
            for date_str, _ in self.sample_dates:
                if date_str not in self.attendance_data[student_id]:
                    self.attendance_data[student_id][date_str] = random.choice([True, False])
    
    def populate_student_list(self):
        """Populate the student list - handle single student case"""
        # Clear existing rows
        for i in reversed(range(self.list_layout.count())): 
            widget = self.list_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        current_date_str = self.current_date
        
        for student in self.students:
            student_id = student["id"]
            
            # Get attendance status for current date
            is_present = self.attendance_data.get(student_id, {}).get(current_date_str, True)
            
            # Create row
            row = AttendanceRow(student, current_date_str, is_present)
            row.attendance_changed.connect(self.on_attendance_changed)
            
            self.list_layout.addWidget(row)
        
        self.update_statistics()
        
        # If only one student, adjust the UI
        if len(self.students) == 1:
            self.adjust_for_single_student()
    
    def adjust_for_single_student(self):
        """Adjust UI when showing only one student"""
        # Hide "Mark All" buttons since they don't make sense for one student
        self.mark_all_present_btn.hide()
        self.mark_all_absent_btn.hide()
        
        # Update stats label to be more appropriate
        if hasattr(self, 'stats_label'):
            self.stats_label.setText("Your attendance for today")
    
    def update_statistics(self):
        """Update footer statistics - adjusted for single student"""
        if self.mode == "mark":
            present_count = 0
            total = 0
            
            for i in range(self.list_layout.count()):
                item = self.list_layout.itemAt(i)
                if item and (widget := item.widget()):
                    if isinstance(widget, AttendanceRow):
                        total += 1
                        if widget.is_present:
                            present_count += 1
            
            absent_count = total - present_count
            
            if total == 1:
                # Single student view
                status = "Present" if present_count == 1 else "Absent"
                self.stats_label.setText(
                    f"Status: <b style='color: {'#2d6a4f' if present_count == 1 else '#c9485b'};'>{status}</b> | "
                    f"Date: <b>{self.current_date}</b>"
                )
            else:
                # Multiple students view
                self.stats_label.setText(
                    f"Present: <b style='color: #2d6a4f;'>{present_count}</b> | "
                    f"Absent: <b style='color: #c9485b;'>{absent_count}</b> | "
                    f"Total: <b>{total}</b> | "
                    f"Date: <b>{self.current_date}</b>"
                )
        else:
            # For overview view
            total_absences = 0
            num_students = len(self.students)
            
            for student_idx in range(num_students):
                row = student_idx + 1
                absences_item = self.overview_widget.table.item(row, 2)
                if absences_item:
                    total_absences += int(absences_item.text())
            
            total_possible = num_students * (self.overview_widget.table.columnCount() - 3)
            total_present = total_possible - total_absences
            
            if num_students == 1:
                # Single student overview
                self.stats_label.setText(
                    f"Your attendance overview | "
                    f"Present: <b style='color: #2d6a4f;'>{total_present}</b> | "
                    f"Absent: <b style='color: #c9485b;'>{total_absences}</b>"
                )
            else:
                # Multiple students overview
                self.stats_label.setText(
                    f"Overall: Present: <b style='color: #2d6a4f;'>{total_present}</b> | "
                    f"Absent: <b style='color: #c9485b;'>{total_absences}</b> | "
                    f"Total Records: <b>{total_possible}</b> | "
                    f"Students: <b>{num_students}</b>"
                )
    
    def populate_overview_view(self):
        """Populate the overview view"""
        # Convert dates to the format expected by AttendanceTableWidget
        dates = [(date_str, "Present") for date_str, _ in self.sample_dates]
        
        # Load data into the table
        self.overview_widget.load_data(self.students, dates)
        
        # Load attendance data for each student and date
        num_students = len(self.students)
        num_dates = len(dates)
        
        for student_idx in range(num_students):
            row = student_idx + 1
            student_id = self.students[student_idx]["id"]
            
            for date_idx in range(num_dates):
                col = 3 + date_idx
                date_str = dates[date_idx][0]
                
                # Get attendance status from stored data
                is_present = self.attendance_data.get(student_id, {}).get(date_str, True)
                
                # In the table, we need to set the checkbox state based on the mode
                # For "Present" mode: checked = present, unchecked = absent
                # For "Absent" mode: checked = absent, unchecked = present
                mode = self.overview_widget.attendance_data[row][col]['mode']
                
                if mode == "Present":
                    checked = is_present  # Present = checked, Absent = unchecked
                else:  # Absent mode
                    checked = not is_present  # Absent = checked, Present = unchecked
                
                self.overview_widget.attendance_data[row][col]['checked'] = checked
                
                # Update the UI
                cell_widget = self.overview_widget.table.cellWidget(row, col)
                if cell_widget:
                    checkbox = cell_widget.findChild(QCheckBox)
                    label = cell_widget.findChild(QLabel)
                    
                    if checkbox and label:
                        checkbox.blockSignals(True)
                        checkbox.setChecked(checked)
                        checkbox.blockSignals(False)
                        
                        self.overview_widget.update_checkbox_style(checkbox, label, mode, checked)
        
        self.overview_widget.update_absence_counts()
    
    def on_view_mode_changed(self, mode_text):
        """Handle view mode change with appropriate controls"""
        if mode_text == "Mark Attendance":
            self.show_mark_attendance_view()
            self.mode = "mark"
            # Show date picker and buttons
            self.date_picker.show()
            self.mark_all_present_btn.show()
            self.mark_all_absent_btn.show()
            self.save_btn.show()
        else:  # "Overview"
            self.show_overview_view()
            self.mode = "overview"
            # Hide editing controls for overview
            self.date_picker.hide()
            self.mark_all_present_btn.hide()
            self.mark_all_absent_btn.hide()
            self.save_btn.hide()
        
        # Update statistics based on current view
        self.update_statistics()
    
    def show_mark_attendance_view(self):
        """Show mark attendance view"""
        self.overview_widget.hide()
        self.mark_attendance_widget.show()
    
    def show_overview_view(self):
        """Show overview view"""
        self.mark_attendance_widget.hide()
        self.overview_widget.show()
    
    def on_date_changed(self, date):
        """Handle date change for mark attendance view"""
        new_date = date.toString("MMMM d")
        self.current_date = new_date
        
        # Ensure attendance data exists for new date
        for student in self.students:
            student_id = student["id"]
            if student_id not in self.attendance_data:
                self.attendance_data[student_id] = {}
            if new_date not in self.attendance_data[student_id]:
                self.attendance_data[student_id][new_date] = True  # Default to present
        
        # Update all rows for new date
        for i in range(self.list_layout.count()):
            item = self.list_layout.itemAt(i)
            if item and (widget := item.widget()):
                if isinstance(widget, AttendanceRow):
                    student_id = widget.student_data["id"]
                    is_present = self.attendance_data[student_id].get(new_date, True)
                    widget.update_date(new_date, is_present)
        
        self.update_statistics()
    
    def on_attendance_changed(self, student_id, date, is_present):
        """Handle attendance change from rows or table"""
        if student_id not in self.attendance_data:
            self.attendance_data[student_id] = {}
        
        self.attendance_data[student_id][date] = is_present
        
        # Update the other view if needed
        if self.mode == "mark":
            # Update overview view if it contains this date
            for i in range(self.overview_widget.table.columnCount() - 3):
                col = 3 + i
                date_data = self.overview_widget.attendance_data.get(1, {}).get(col, {})
                if date_data.get('date') == date:
                    # Find the student row
                    for student_idx, student in enumerate(self.students):
                        if student["id"] == student_id:
                            row = student_idx + 1
                            mode = self.overview_widget.attendance_data[row][col]['mode']
                            
                            if mode == "Present":
                                checked = is_present  # Present = checked, Absent = unchecked
                            else:  # Absent mode
                                checked = not is_present  # Absent = checked, Present = unchecked
                            
                            self.overview_widget.attendance_data[row][col]['checked'] = checked
                            
                            # Update the UI
                            cell_widget = self.overview_widget.table.cellWidget(row, col)
                            if cell_widget:
                                checkbox = cell_widget.findChild(QCheckBox)
                                label = cell_widget.findChild(QLabel)
                                
                                if checkbox and label:
                                    checkbox.blockSignals(True)
                                    checkbox.setChecked(checked)
                                    checkbox.blockSignals(False)
                                    
                                    self.overview_widget.update_checkbox_style(checkbox, label, mode, checked)
                            
                            self.overview_widget.update_absence_counts()
                            break
        
        self.update_statistics()
    
    def mark_all_present(self):
        """Mark all students as present - only in Mark Attendance mode"""
        if self.mode == "mark":
            for i in range(self.list_layout.count()):
                item = self.list_layout.itemAt(i)
                if item and (widget := item.widget()):
                    if isinstance(widget, AttendanceRow):
                        widget.set_attendance(True)
        else:
            # Overview mode is read-only, don't do anything
            return
    
    def mark_all_absent(self):
        """Mark all students as absent - only in Mark Attendance mode"""
        if self.mode == "mark":
            for i in range(self.list_layout.count()):
                item = self.list_layout.itemAt(i)
                if item and (widget := item.widget()):
                    if isinstance(widget, AttendanceRow):
                        widget.set_attendance(False)
        else:
            # Overview mode is read-only, don't do anything
            return
    
    def update_statistics(self):
        """Update footer statistics - adjusted for role and view"""
        if self.mode == "mark":
            present_count = 0
            total = 0
            
            for i in range(self.list_layout.count()):
                item = self.list_layout.itemAt(i)
                if item and (widget := item.widget()):
                    if isinstance(widget, AttendanceRow):
                        total += 1
                        if widget.is_present:
                            present_count += 1
            
            absent_count = total - present_count
            
            if total == 1:
                # Single student view (for teachers viewing one student)
                status = "Present" if present_count == 1 else "Absent"
                self.stats_label.setText(
                    f"Status: <b style='color: {'#2d6a4f' if present_count == 1 else '#c9485b'};'>{status}</b> | "
                    f"Date: <b>{self.current_date}</b>"
                )
            else:
                # Multiple students view
                self.stats_label.setText(
                    f"Present: <b style='color: #2d6a4f;'>{present_count}</b> | "
                    f"Absent: <b style='color: #c9485b;'>{absent_count}</b> | "
                    f"Total: <b>{total}</b> | "
                    f"Date: <b>{self.current_date}</b>"
                )
        else:
            # Overview view
            if len(self.students) == 1:
                # Single student overview
                student_name = self.students[0]["name"] if self.students else "Student"
                self.stats_label.setText(
                    f"<b>{student_name}</b> - Attendance Overview | "
                    f"Showing last 7 days"
                )
            else:
                # Multiple students overview
                num_students = len(self.students)
                self.stats_label.setText(
                    f"Class Attendance Overview | "
                    f"<b>{num_students}</b> students | "
                    f"Showing last 7 days"
                )
    
    def save_attendance(self):
        """Save attendance data"""
        if self.mode == "mark":
            present_count = 0
            total = 0
            
            for i in range(self.list_layout.count()):
                item = self.list_layout.itemAt(i)
                if item and (widget := item.widget()):
                    if isinstance(widget, AttendanceRow):
                        total += 1
                        if widget.is_present:
                            present_count += 1
            
            absent_count = total - present_count
            
            # In a real application, you would save to database here
            print(f"Attendance saved for {self.current_date}:")
            print(f"Present: {present_count}, Absent: {absent_count}")
            
            # Show simple confirmation
            self.stats_label.setText(
                f"✓ Saved! Present: {present_count}, Absent: {absent_count} | Date: {self.current_date}"
            )
        else:
            # Save all dates
            total_records = 0
            present_count = 0
            absent_count = 0
            
            num_students = len(self.students)
            num_dates = self.overview_widget.table.columnCount() - 3
            
            for student_idx in range(num_students):
                row = student_idx + 1
                for date_idx in range(num_dates):
                    col = 3 + date_idx
                    data = self.overview_widget.attendance_data.get(row, {}).get(col, {})
                    if data:
                        total_records += 1
                        mode = data.get('mode', 'Present')
                        checked = data.get('checked', False)
                        
                        is_absent = (mode == "Present" and not checked) or (mode == "Absent" and checked)
                        
                        if is_absent:
                            absent_count += 1
                        else:
                            present_count += 1
            
            print(f"Attendance saved for all {num_dates} dates:")
            print(f"Present: {present_count}, Absent: {absent_count}, Total Records: {total_records}")
            
            # Show simple confirmation
            self.stats_label.setText(
                f"✓ Saved! Present: {present_count}, Absent: {absent_count} | Total Dates: {num_dates}"
            )
    def set_editable(self, editable: bool):
        """Enable or disable editing of attendance"""
        # Enable/disable save button
        self.save_btn.setEnabled(editable)
        
        # Enable/disable mark all buttons
        self.mark_all_present_btn.setEnabled(editable)
        self.mark_all_absent_btn.setEnabled(editable)
        
        # Enable/disable checkboxes in student rows
        for row in self.student_rows:
            if hasattr(row, 'present_check'):
                row.present_check.setEnabled(editable)
            if hasattr(row, 'absent_check'):
                row.absent_check.setEnabled(editable)


def load_fonts():
    """Load Poppins font from resources or use system font"""
    # Try to load Poppins font, fallback to system font if not available
    font_families = QFontDatabase.families()
    poppins_variants = [f for f in font_families if 'poppins' in f.lower()]
    
    if poppins_variants:
        return poppins_variants[0]  # Use the first available Poppins variant
    else:
        print("Poppins font not found. Using system default font.")
        return "Segoe UI"  # Fallback font


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Load and set Poppins font
    poppins_font = load_fonts()
    font = QFont(poppins_font, 10)
    app.setFont(font)
    
    widget = AttendanceWidget()
    widget.show()
    
    sys.exit(app.exec())