from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QComboBox, QTextEdit, QFrame,
                             QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
                             QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
import datetime
import os
from ...utils.icon_utils import IconLoader


class FileUploadDialog(QDialog):
    """
    Bulk File Upload Dialog - Modal popup for uploading multiple files
    
    This dialog provides a form interface for uploading multiple files with:
    - Multiple file selection
    - Selected files list with remove capability
    - Upload date display
    - Category and Collection dropdowns (applied to all files)
    - Bulk file description text area
    - Upload progress bar
    - Bulk upload action button
    
    Signals:
        file_uploaded: Emitted when each file is successfully uploaded
    
    Args:
        parent (QWidget): Parent widget (typically AdminDash)
        collection_id (int, optional): Pre-select collection for file upload
        username (str): Current user's username
        role (str): Current user's role
    """
    
    # Signal emitted when each file is uploaded
    file_uploaded = pyqtSignal(dict)
    
    def __init__(self, parent=None, collection_id=None, username=None, role=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Bulk File Upload")
        self.setFixedSize(550, 750)
        
        self.selected_files = []  # List of file paths
        self.collection_id = collection_id
        self.username = username  # Store username
        self.role = role  # Store role (can be "student-org_officer")
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI components"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # ========== TITLE ==========
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel("Bulk File Upload")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529; padding: 10px 0;")
        title_layout.addWidget(title_label)
        main_layout.addLayout(title_layout)
        
        # ========== FILE ICON ==========
        icon_layout = QHBoxLayout()
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        file_icon = IconLoader.create_icon_label("document.png", size=(64, 64), alignment=Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(file_icon)
        main_layout.addLayout(icon_layout)
        
        # ========== FILE SELECTION BUTTON ==========
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        select_files_btn = QPushButton("Select Files")
        select_files_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                padding: 10px 24px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        select_files_btn.clicked.connect(self.handle_select_files)
        
        button_layout.addWidget(select_files_btn)
        main_layout.addLayout(button_layout)
        
        # ========== SELECTED FILES LIST ==========
        files_label = QLabel("Selected Files:")
        files_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057; margin-top: 10px;")
        main_layout.addWidget(files_label)
        
        self.files_list = QListWidget()
        self.files_list.setMinimumHeight(180)
        self.files_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #e9ecef;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
        """)
        main_layout.addWidget(self.files_list)
        
        # Remove selected file button
        remove_file_btn = QPushButton("Remove Selected")
        remove_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 6px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        remove_file_btn.clicked.connect(self.handle_remove_file)
        main_layout.addWidget(remove_file_btn)
        
        # ========== UPLOAD DATE ==========
        date_layout = QHBoxLayout()
        date_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        upload_date = QLabel(f"Upload Date: {datetime.datetime.now().strftime('%m/%d/%Y')}")
        upload_date.setStyleSheet("font-size: 13px; color: #6c757d; padding: 10px 0;")
        date_layout.addWidget(upload_date)
        main_layout.addLayout(date_layout)
        
        # ========== FORM FIELDS FRAME ==========
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)
        
        # Style for labels and inputs
        label_style = "color: #6c757d; font-weight: bold; min-width: 100px; font-size: 13px; background: transparent; border: none; padding: 0;"
        combo_style = """
            QComboBox {
                background-color: white;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px 12px;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #80bdff;
            }
        """
        
        # ========== CATEGORY DROPDOWN ==========
        category_layout = QHBoxLayout()
        category_label = QLabel("Category")
        category_label.setStyleSheet(label_style)
        category_label.setFixedWidth(100)
        
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet(combo_style)
        self.category_combo.addItems(["None", "Syllabus", "Memo", "Forms", "Report", "Other"])
        
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        form_layout.addLayout(category_layout)
        
        # ========== COLLECTION DROPDOWN ==========
        collection_layout = QHBoxLayout()
        collection_label = QLabel("Collection")
        collection_label.setStyleSheet(label_style)
        collection_label.setFixedWidth(100)
        
        self.collection_combo = QComboBox()
        self.collection_combo.setStyleSheet(combo_style)
        self._load_collections()
        
        collection_layout.addWidget(collection_label)
        collection_layout.addWidget(self.collection_combo)
        form_layout.addLayout(collection_layout)
        
        form_frame.setLayout(form_layout)
        main_layout.addWidget(form_frame)
        
        # ========== FILE DESCRIPTION ==========
        desc_frame = QFrame()
        desc_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        desc_layout = QVBoxLayout()
        desc_layout.setSpacing(10)
        
        desc_label = QLabel("Description (applied to all files, optional):")
        desc_label.setStyleSheet("color: #495057; font-weight: bold; font-size: 14px; background: transparent; border: none; padding: 0;")
        desc_layout.addWidget(desc_label)
        
        self.description_text = QTextEdit()
        self.description_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                color: #495057;
            }
            QTextEdit:focus {
                border-color: #80bdff;
            }
        """)
        self.description_text.setPlaceholderText("Enter description for all files...")
        self.description_text.setMinimumHeight(100)
        desc_layout.addWidget(self.description_text)
        
        desc_frame.setLayout(desc_layout)
        main_layout.addWidget(desc_frame)
        
        # ========== PROGRESS BAR ==========
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
                background-color: #e9ecef;
                height: 24px;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setVisible(False)  # Hidden until upload starts
        main_layout.addWidget(self.progress_bar)
        
        # ========== UPLOAD BUTTON ==========
        upload_btn = QPushButton("Upload All Files")
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 12px 20px;
                border: none;
                border-radius: 6px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        upload_btn.clicked.connect(self.handle_upload)
        main_layout.addWidget(upload_btn)
        
        self.setLayout(main_layout)
    
    def _load_collections(self):
        """Load collections from data and populate dropdown"""
        from ...services.document_crud_service import DocumentCRUDService
        
        crud_service = DocumentCRUDService()
        collections = crud_service.get_all_collections()
        
        # Add "None" option
        self.collection_combo.addItem("None (Standalone)", None)
        
        # Add all collections
        for collection in collections:
            self.collection_combo.addItem(collection["name"], collection["id"])
        
        # Pre-select collection if provided
        if self.collection_id:
            for i in range(self.collection_combo.count()):
                if self.collection_combo.itemData(i) == self.collection_id:
                    self.collection_combo.setCurrentIndex(i)
                    break
    
    def handle_select_files(self):
        """Handle multiple file selection button click"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files (Multiple)",
            "",
            "All Files (*);;PDF Files (*.pdf);;Word Documents (*.docx *.doc);;Excel Files (*.xlsx *.xls);;Images (*.png *.jpg *.jpeg)"
        )
        
        if file_paths:
            # Add selected files to the list
            for file_path in file_paths:
                if file_path not in self.selected_files:
                    self.selected_files.append(file_path)
                    filename = os.path.basename(file_path)
                    self.files_list.addItem(filename)
            
            print(f"{len(file_paths)} file(s) selected. Total: {len(self.selected_files)}")
    
    def handle_remove_file(self):
        """Handle removing a file from the selected files list"""
        current_row = self.files_list.currentRow()
        if current_row >= 0:
            # Remove from list widget
            self.files_list.takeItem(current_row)
            # Remove from selected files
            del self.selected_files[current_row]
            print(f"File removed. Remaining: {len(self.selected_files)}")
    
    def handle_upload(self):
        """Handle bulk upload button click with progress tracking"""
        # Validate file selection
        if not self.selected_files:
            QMessageBox.warning(
                self,
                "No Files Selected",
                "Please select at least one file to upload."
            )
            return
        
        category = self.category_combo.currentText()
        collection_id = self.collection_combo.currentData()
        description = self.description_text.toPlainText()
        
        # Import services
        from ...services.file_storage_service import FileStorageService
        from ...services.document_crud_service import DocumentCRUDService
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.selected_files))
        self.progress_bar.setValue(0)
        
        # Track upload results
        successful_uploads = 0
        failed_uploads = []
        
        # Process each file
        for index, file_path in enumerate(self.selected_files):
            try:
                filename = os.path.basename(file_path)
                base_filename = os.path.splitext(filename)[0]
                
                # Check for duplicate filename
                storage_service = FileStorageService()
                is_duplicate = storage_service.check_duplicate_filename(base_filename)
                
                # Auto-rename if duplicate (no prompt for bulk uploads)
                if is_duplicate:
                    unique_filename = storage_service.generate_unique_filename(base_filename)
                    _, ext = os.path.splitext(file_path)
                    filename = unique_filename + ext
                    print(f"Duplicate detected. Renamed to: {filename}")
                
                # Upload based on collection or standalone
                if collection_id is not None:
                    # Upload to collection
                    result = self._upload_to_collection(
                        file_path, filename, category, collection_id, storage_service
                    )
                else:
                    # Standalone upload
                    result = self._upload_standalone(
                        file_path, filename, category, description
                    )
                
                if result['success']:
                    successful_uploads += 1
                    # Emit signal for each successful upload
                    self.file_uploaded.emit(result['file_data'])
                else:
                    failed_uploads.append((filename, result.get('error', 'Unknown error')))
                
            except Exception as e:
                failed_uploads.append((os.path.basename(file_path), str(e)))
            
            # Update progress bar
            self.progress_bar.setValue(index + 1)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Show results summary
        self._show_upload_summary(successful_uploads, failed_uploads)
    
    def _upload_to_collection(self, file_path, filename, category, collection_id, storage_service):
        """Upload a single file to a collection"""
        from ...services.document_crud_service import DocumentCRUDService
        
        try:
            # Save physical file
            result = storage_service.save_file(
                file_path, 
                filename, 
                category if category != "None" else None
            )
            
            if not result['success']:
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to save file')
                }
            
            # Add to collection (this also adds to uploaded_files automatically)
            crud_service = DocumentCRUDService()
            collection_result = crud_service.add_file_to_collection(
                collection_id,
                result['filename'],
                result['file_path'],
                category if category != "None" else None,
                result['extension'],
                self.username,
                self.role
            )
            
            if collection_result.get('success'):
                return {
                    'success': True,
                    'file_data': collection_result.get('file')
                }
            else:
                return {
                    'success': False,
                    'error': collection_result.get('error', 'Failed to add file to collection')
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _upload_standalone(self, file_path, filename, category, description):
        """Upload a single file as standalone (not in collection)"""
        from ...controller.document_controller import DocumentController
        
        try:
            controller = DocumentController(
                self.username, 
                [], 
                self.role, 
                ""
            )
            
            # Get collection name from combo box (not ID)
            collection_name = self.collection_combo.currentText()
            if collection_name == "None (Standalone)":
                collection_name = None
            
            success, message, file_data = controller.upload_file(
                file_path,
                custom_name=filename,
                category=category if category != "None" else None,
                collection=collection_name,  # Pass collection name
                description=description,
                force_override=False  # Auto-rename duplicates in bulk upload
            )
            
            if success:
                return {
                    'success': True,
                    'file_data': file_data
                }
            else:
                return {
                    'success': False,
                    'error': message
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _show_upload_summary(self, successful_uploads, failed_uploads):
        """Show summary dialog after bulk upload"""
        total = successful_uploads + len(failed_uploads)
        
        if len(failed_uploads) == 0:
            # All successful
            QMessageBox.information(
                self,
                "Upload Complete",
                f"Successfully uploaded {successful_uploads} file(s)!"
            )
            self.accept()  # Close dialog
        elif successful_uploads == 0:
            # All failed
            error_details = "\n".join([f"• {fname}: {error}" for fname, error in failed_uploads[:5]])
            if len(failed_uploads) > 5:
                error_details += f"\n... and {len(failed_uploads) - 5} more"
            
            QMessageBox.critical(
                self,
                "Upload Failed",
                f"Failed to upload {len(failed_uploads)} file(s):\n\n{error_details}"
            )
        else:
            # Mixed results
            error_details = "\n".join([f"• {fname}: {error}" for fname, error in failed_uploads[:5]])
            if len(failed_uploads) > 5:
                error_details += f"\n... and {len(failed_uploads) - 5} more"
            
            QMessageBox.warning(
                self,
                "Upload Completed with Errors",
                f"Uploaded {successful_uploads} of {total} file(s) successfully.\n\n"
                f"Failed uploads:\n{error_details}"
            )
            self.accept()  # Close dialog even with partial success
