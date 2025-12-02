from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt
import csv
import os

class BulkUploadDialog(QDialog):
    """
    Bulk Upload Dialog for importing students from CSV file
    
    Expected CSV format:
    id_number,full_name,year_level
    20223010001,Dela Cruz Juan,1
    20223010002,Santos Maria,2
    """
    
    def __init__(self, ui_path=None):
        """Initialize the bulk upload dialog"""
        super().__init__()
        
        # Load UI file
        if ui_path is None:
            import os

            current_dir = os.path.dirname(os.path.abspath(__file__))

            # Get project root (enrollment_ui/)
            project_root = os.path.dirname(current_dir)

            possible_paths = [
            os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "ui", "Academics", "Enrollment", "bulk_upload_dialog.ui")),
            os.path.normpath(os.path.join(os.path.dirname(__file__), "ui", "Academics", "Enrollment", "bulk_upload_dialog.ui")),
            os.path.normpath(os.path.join(os.path.dirname(__file__), "bulk_upload_dialog.ui")),
            "frontend/ui/Academics/Enrollment/bulk_upload_dialog.ui",
            "ui/Academics/Enrollment/bulk_upload_dialog.ui",
            "ui/Academics/Enrollment/bulk_upload_dialog.ui",
        ]
                    
            # Debug: print paths being checked
            print("Searching for bulk_upload_dialog.ui in:")
            for path in possible_paths:
                exists = os.path.exists(path)
                print(f"  {'✓' if exists else '✗'} {path}")
            
            for path in possible_paths:
                if os.path.exists(path):
                    ui_path = path
                    print(f"Using: {ui_path}")
                    break
            else:
                raise FileNotFoundError(
                    f"Could not find bulk_upload_dialog.ui\n"
                    f"Current directory: {current_dir}\n"
                    f"Project root: {project_root}\n"
                    f"Searched in:\n" + "\n".join(f"  - {p}" for p in possible_paths)
                )
        
        uic.loadUi(ui_path, self)
        
        # Store file path and parsed students
        self.selected_file_path = None
        self.parsed_students = []
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        self.uploadFrame.setAcceptDrops(True)
        
        # Setup icon (file icon)
        self.iconLabel.setText("📄")
        
        # Connect signals
        self._connect_signals()


    # ==================== SETUP ====================
    def browse_file(self):
        """Open file browser to select CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            self.load_csv(file_path)
    
    def load_csv(self, file_path):
        """Read and parse CSV file"""
        try:
            students = []
            
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Check if required columns exist
                if reader.fieldnames:
                    required = {'id_number', 'full_name', 'year_level'}
                    if not required.issubset(reader.fieldnames):
                        raise ValueError(
                            f"CSV must contain columns: id_number, full_name, year_level\n"
                            f"Found: {', '.join(reader.fieldnames)}"
                        )
                
                # Parse rows
                for row in reader:
                    if row.get('id_number') and row.get('full_name') and row.get('year_level'):
                        students.append({
                            'id': row['id_number'].strip(),
                            'name': row['full_name'].strip(),
                            'year': row['year_level'].strip()
                        })
            
            if students:
                self.parsed_students = students
                file_name = os.path.basename(file_path)
                self.fileInfoLabel.setText(f"📁 {file_name}")
                self.statusLabel.setText(f"✓ Found {len(students)} student(s)")
                self.statusLabel.setStyleSheet("color: #4CAF50; font-weight: 600;")
                self.uploadButton.setEnabled(True)
                
                # Change upload frame to green
                self.uploadFrame.setStyleSheet("""
                    QFrame#uploadFrame {
                        background-color: #E8F5E9;
                        border: 2px solid #4CAF50;
                        border-radius: 8px;
                    }
                """)
            else:
                QMessageBox.warning(self, "Empty File", "No valid student records found.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read CSV:\n{str(e)}")
    
    def download_template(self):
        """Save CSV template"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Template", "student_template.csv", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['id_number', 'full_name', 'year_level'])
                    writer.writerow(['20223010001', 'Dela Cruz, Juan', '1'])
                    writer.writerow(['20223010002', 'Santos, Maria', '2'])
                
                QMessageBox.information(self, "Success", f"Template saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save template:\n{str(e)}")
    
    def upload(self):
        """Confirm and accept upload"""
        if not self.parsed_students:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Upload",
            f"Upload {len(self.parsed_students)} student(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.accept()
    
    def get_students(self):
        """Return uploaded students"""
        return self.parsed_students.copy()
    
    # ==================== SETUP ====================
    
    def _connect_signals(self):
        """Connect all signal handlers"""
        self.browseButton.clicked.connect(self._on_browse)
        self.downloadTemplateButton.clicked.connect(self._on_download_template)
        self.cancelButton.clicked.connect(self.reject)
        self.uploadButton.clicked.connect(self._on_upload)
    
    # ==================== FILE SELECTION ====================
    
    def _on_browse(self):
        """Open file dialog to select CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*.*)"
        )
        
        if file_path:
            self._load_file(file_path)
    
    def _load_file(self, file_path):
        """Load and parse CSV file"""
        try:
            # Read and parse CSV
            students = self._parse_csv(file_path)
            
            if not students:
                QMessageBox.warning(
                    self,
                    "Empty File",
                    "The CSV file contains no valid student records."
                )
                return
            
            # Store parsed data
            self.selected_file_path = file_path
            self.parsed_students = students
            
            # Update UI
            file_name = os.path.basename(file_path)
            self.fileInfoLabel.setText(f"📁 {file_name}")
            self.statusLabel.setText(f"✓ Found {len(students)} student(s)")
            self.statusLabel.setStyleSheet("color: #4CAF50; font-weight: 600;")
            self.uploadButton.setEnabled(True)
            
            # Change upload frame appearance
            self.uploadFrame.setStyleSheet("""
                QFrame#uploadFrame {
                    background-color: #E8F5E9;
                    border: 2px solid #4CAF50;
                    border-radius: 8px;
                }
            """)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to read CSV file:\n{str(e)}"
            )
    
    def _parse_csv(self, file_path):
        """
        Parse CSV file and extract student data
        
        Expected format:
        id_number,full_name,year_level
        20223010001,Dela Cruz Juan,1
        
        Returns:
            list: List of student dictionaries
        """
        students = []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            # Check if required columns exist
            required_columns = {'id_number', 'full_name', 'year_level'}
            if not required_columns.issubset(csv_reader.fieldnames):
                raise ValueError(
                    f"CSV must contain columns: {', '.join(required_columns)}\n"
                    f"Found columns: {', '.join(csv_reader.fieldnames)}"
                )
            
            # Parse each row
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (1 is header)
                # Skip empty rows
                if not any(row.values()):
                    continue
                
                # Validate data
                id_number = row['id_number'].strip()
                full_name = row['full_name'].strip()
                year_level = row['year_level'].strip()
                
                if not id_number or not full_name or not year_level:
                    print(f"Warning: Skipping row {row_num} - incomplete data")
                    continue
                
                # Add student
                students.append({
                    'id': id_number,
                    'name': full_name,
                    'year': year_level
                })
        
        return students
    
    # ==================== DRAG AND DROP ====================
    
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop event"""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        
        if files:
            file_path = files[0]
            
            # Check if it's a CSV file
            if file_path.lower().endswith('.csv'):
                self._load_file(file_path)
            else:
                QMessageBox.warning(
                    self,
                    "Invalid File",
                    "Please drop a CSV file."
                )
    
    # ==================== TEMPLATE DOWNLOAD ====================
    
    def _on_download_template(self):
        """Download CSV template file"""
        # Ask where to save
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV Template",
            "student_template.csv",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                # Create template CSV
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    
                    # Write header
                    writer.writerow(['id_number', 'full_name', 'year_level'])
                    
                    # Write sample data
                    writer.writerow(['20223010001', 'Dela Cruz, Juan', '1'])
                    writer.writerow(['20223010002', 'Santos, Maria', '2'])
                    writer.writerow(['20223010003', 'Reyes, Pedro', '3'])
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Template saved to:\n{file_path}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save template:\n{str(e)}"
                )
    
    # ==================== UPLOAD ====================
    
    def _on_upload(self):
        """Process the uploaded file"""
        if not self.parsed_students:
            return
        
        # Show confirmation
        reply = QMessageBox.question(
            self,
            "Confirm Upload",
            f"Upload {len(self.parsed_students)} student(s) from CSV?\n\n"
            f"This will add all students to the enrollment list.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Accept dialog and pass data back
            self.accept()
    
    # ==================== PUBLIC METHODS ====================
    
    def get_students(self):
        """
        Get the parsed students from the CSV file
        
        Returns:
            list: List of student dictionaries
        """
        return self.parsed_students.copy()


# ==================== TESTING ====================

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
    
    def show_bulk_dialog():
        """Test the bulk upload dialog"""
        dialog = BulkUploadDialog()
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            students = dialog.get_students()
            
            if students:
                print("\n=== Uploaded Students ===")
                for s in students:
                    print(f"ID: {s['id']}, Name: {s['name']}, Year: {s['year']}")
                
                status_label.setText(f"Uploaded {len(students)} student(s)")
                
                # Show summary
                QMessageBox.information(
                    None,
                    "Upload Complete",
                    f"Successfully uploaded {len(students)} student(s)!"
                )
        else:
            status_label.setText("Upload cancelled")
    
    app = QApplication(sys.argv)
    
    window = QWidget()
    layout = QVBoxLayout()
    
    title = QLabel("Bulk Upload Dialog - Test")
    title.setStyleSheet("font-size: 14pt; font-weight: bold; margin: 10px;")
    layout.addWidget(title)
    
    info = QLabel(
        "This dialog allows uploading students from CSV.\n"
        "Click 'Download CSV Template' first to see the format."
    )
    info.setStyleSheet("color: #666; margin: 10px;")
    info.setWordWrap(True)
    layout.addWidget(info)
    
    btn_open = QPushButton("Open Bulk Upload Dialog")
    btn_open.clicked.connect(show_bulk_dialog)
    btn_open.setMinimumHeight(50)
    layout.addWidget(btn_open)
    
    status_label = QLabel("Ready")
    status_label.setStyleSheet("color: #666; margin: 10px;")
    layout.addWidget(status_label)
    
    window.setLayout(layout)
    window.setWindowTitle("Test - Bulk Upload")
    window.resize(450, 250)
    window.show()
    
    sys.exit(app.exec())