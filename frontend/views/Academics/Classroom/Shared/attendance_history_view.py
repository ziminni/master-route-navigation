# attendance_history_view.py - Updated with role-based access
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
import datetime

class AttendanceHistoryView(QDialog):
    """Attendance history view with role-based access"""
    
    def __init__(self, attendance_controller, class_id, class_name, user_role="teacher", parent=None):
        super().__init__(parent)
        self.attendance_controller = attendance_controller
        self.class_id = class_id
        self.class_name = class_name
        self.user_role = user_role.lower()
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        role_title = {
            "teacher": "Teacher View",
            "assistant": "Assistant View",
            "student": "Your Attendance",
            "parent": "Student Attendance"
        }.get(self.user_role, "View")
        
        self.setWindowTitle(f"Attendance History - {self.class_name} ({role_title})")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title with role indicator
        title_text = f"Attendance History: {self.class_name}"
        if self.user_role in ["student", "parent"]:
            title_text += f" - {role_title}"
        
        title = QLabel(title_text)
        title_font = QFont("Poppins", 14, QFont.Weight.Bold)
        title.setFont(title_font)
        
        if self.user_role == "teacher":
            title.setStyleSheet("color: #1e5a3a;")
        elif self.user_role == "assistant":
            title.setStyleSheet("color: #2d6a4f;")
        elif self.user_role == "student":
            title.setStyleSheet("color: #3a7ca5;")
        else:
            title.setStyleSheet("color: #6c757d;")
            
        layout.addWidget(title)
        
        # Role badge
        role_badge = QLabel(f"Role: {self.user_role.capitalize()}")
        role_badge.setStyleSheet("""
            font-size: 12px; 
            color: white; 
            background-color: #6c757d; 
            padding: 4px 12px; 
            border-radius: 12px;
        """)
        layout.addWidget(role_badge)
        
        # Date range info
        self.date_range_label = QLabel()
        self.date_range_label.setStyleSheet("font-size: 13px; color: #6c757d;")
        layout.addWidget(self.date_range_label)
        
        # Table setup based on role
        if self.user_role in ["teacher", "assistant", "parent"]:
            self.setup_class_table()
        else:  # student
            self.setup_student_table()
        
        layout.addWidget(self.table)
        
        # Summary
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("""
            font-size: 13px;
            color: #495057;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 6px;
            border: 1px solid #dee2e6;
        """)
        layout.addWidget(self.summary_label)
        
        # Export button for teachers and assistants
        if self.user_role in ["teacher", "assistant"]:
            export_btn = QPushButton("Export to CSV")
            export_btn.setStyleSheet("""
                QPushButton {
                    font-family: 'Poppins';
                    background-color: #28a745;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 600;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            export_btn.clicked.connect(self.export_data)
            
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(export_btn)
            layout.addLayout(btn_layout)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                font-family: 'Poppins';
                background-color: #6c757d;
                color: white;
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: 600;
                border: none;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        close_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
    
    def setup_class_table(self):
        """Setup table for class-wide view"""
        self.table = QTableWidget()
        if self.user_role in ["teacher", "assistant"]:
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels([
                "Date", "Present", "Absent", "Total", "Rate"
            ])
        else:  # parent
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels([
                "Date", "Status", "Recorded", "Notes"
            ])
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                font-family: 'Poppins';
                font-size: 12px;
                gridline-color: #dee2e6;
            }
            QHeaderView::section {
                background-color: #2d6a4f;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
            }
        """)
    
    def setup_student_table(self):
        """Setup table for student view"""
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Date", "Status", "Time", "Remarks"
        ])
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                font-family: 'Poppins';
                font-size: 12px;
                gridline-color: #dee2e6;
            }
            QHeaderView::section {
                background-color: #3a7ca5;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
            }
        """)
    
    def load_data(self):
        """Load attendance history data based on role"""
        try:
            # Get last 30 days
            from datetime import datetime, timedelta
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            history = self.attendance_controller.get_attendance_history(
                start_date=str(start_date),
                end_date=str(end_date)
            )
            
            self.date_range_label.setText(f"Showing data from {start_date} to {end_date}")
            
            if not history:
                self.table.setRowCount(0)
                self.summary_label.setText("No attendance records found for the last 30 days.")
                return
            
            self.table.setRowCount(len(history))
            
            if self.user_role in ["teacher", "assistant", "parent"]:
                self.load_class_data(history)
            else:  # student
                self.load_student_data(history)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load history: {str(e)}")
            self.table.setRowCount(0)
            self.summary_label.setText(f"Error: {str(e)}")
    
    def load_class_data(self, history):
        """Load class-wide attendance data"""
        total_present = 0
        total_absent = 0
        total_students = 0
        
        for row, day in enumerate(history):
            date_str = day.get("date", "")
            present = day.get("present_count", 0)
            absent = day.get("absent_count", 0)
            total = day.get("total_students", 0)
            rate = day.get("attendance_rate", 0)
            
            # Format date
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                display_date = date_obj.strftime("%b %d, %Y")
            except:
                display_date = date_str
            
            # Add to table
            self.table.setItem(row, 0, self.create_table_item(display_date))
            self.table.setItem(row, 1, self.create_table_item(str(present)))
            self.table.setItem(row, 2, self.create_table_item(str(absent)))
            
            if self.user_role in ["teacher", "assistant"]:
                self.table.setItem(row, 3, self.create_table_item(str(total)))
                
                # Color code rate
                rate_item = self.create_table_item(f"{rate}%")
                if rate >= 90:
                    rate_item.setBackground(QColor(212, 237, 218))
                elif rate >= 75:
                    rate_item.setBackground(QColor(255, 243, 205))
                else:
                    rate_item.setBackground(QColor(248, 215, 218))
                self.table.setItem(row, 4, rate_item)
            else:  # parent
                # For parent, show status of their child
                status = "Present" if present > 0 else "Absent"
                self.table.setItem(row, 3, self.create_table_item(status))
            
            # Update totals
            total_present += present
            total_absent += absent
            if total > total_students:
                total_students = total
        
        # Update summary
        total_days = len(history)
        if total_days > 0:
            avg_rate = ((total_present / (total_present + total_absent)) * 100) if (total_present + total_absent) > 0 else 0
            
            if self.user_role in ["teacher", "assistant"]:
                self.summary_label.setText(
                    f"Summary: {total_days} days recorded | "
                    f"Average students per day: {total_students/total_days:.1f} | "
                    f"Overall attendance rate: {avg_rate:.1f}%"
                )
            else:  # parent
                self.summary_label.setText(
                    f"Your child attended {total_present} out of {total_days} days "
                    f"({avg_rate:.1f}% attendance rate)"
                )
    
    def load_student_data(self, history):
        """Load student-specific attendance data"""
        present_days = 0
        
        for row, day in enumerate(history):
            date_str = day.get("date", "")
            attendance = day.get("attendance", {})
            
            # Get student's record (assuming student_id = 1 for demo)
            student_record = attendance.get("1", {}) if attendance else {}
            
            # Format date
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                display_date = date_obj.strftime("%b %d, %Y")
            except:
                display_date = date_str
            
            # Add to table
            self.table.setItem(row, 0, self.create_table_item(display_date))
            
            # Status
            is_present = student_record.get("is_present", False)
            status_item = self.create_table_item("✅ Present" if is_present else "❌ Absent")
            if is_present:
                status_item.setBackground(QColor(212, 237, 218))
                present_days += 1
            else:
                status_item.setBackground(QColor(248, 215, 218))
            self.table.setItem(row, 1, status_item)
            
            # Time
            recorded_at = student_record.get("recorded_at", "")
            if recorded_at:
                try:
                    time_obj = datetime.fromisoformat(recorded_at)
                    display_time = time_obj.strftime("%I:%M %p")
                except:
                    display_time = recorded_at
            else:
                display_time = "N/A"
            self.table.setItem(row, 2, self.create_table_item(display_time))
            
            # Remarks
            remarks = "On time" if is_present else "Absent"
            self.table.setItem(row, 3, self.create_table_item(remarks))
        
        # Update summary
        total_days = len(history)
        if total_days > 0:
            attendance_rate = (present_days / total_days) * 100
            self.summary_label.setText(
                f"You attended {present_days} out of {total_days} days "
                f"({attendance_rate:.1f}% attendance rate)"
            )
    
    def export_data(self):
        """Export data to CSV"""
        try:
            from datetime import datetime, timedelta
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            csv_content = self.attendance_controller.export_attendance_to_csv(
                str(start_date), str(end_date)
            )
            
            if csv_content:
                from PyQt6.QtWidgets import QFileDialog
                file_name = f"attendance_history_{self.class_name}_{end_date}.csv"
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Export CSV", file_name, "CSV Files (*.csv)"
                )
                
                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(csv_content)
                    
                    QMessageBox.information(self, "Export Successful", 
                                          f"Data exported to:\n{file_path}")
            else:
                QMessageBox.warning(self, "Export Failed", "No data to export.")
                
        except PermissionError:
            QMessageBox.warning(self, "Permission Denied", 
                              "You do not have permission to export data.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
    
    def create_table_item(self, text):
        """Create a table item"""
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item