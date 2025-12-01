from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QHBoxLayout, QFrame, QLineEdit, QScrollArea,
                             QTableView, QHeaderView,
                             QSizePolicy, QStackedWidget, QMessageBox)
from PyQt6.QtGui import QFont, QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt
from ...controller.document_controller import DocumentController
from ...utils.icon_utils import create_menu_button, create_search_button
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor
from ...widgets.empty_state import EmptyStateWidget


class FacultyDash(QWidget):
    """
    Faculty Dashboard Widget
    
    Faculty can:
    - View their own uploaded files
    - Upload new files (auto-approved)
    - Edit their own files
    - Delete their own files
    - Organize files in collections
    
    Args:
        username (str): The logged-in user's username
        roles (list): List of user roles
        primary_role (str): The user's primary role
        token (str): Authentication token
    """
    
    def __init__(self, username, roles, primary_role, token):
        super().__init__()

        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        
        self.controller = DocumentController(username, roles, primary_role, token)

        # Track collection widgets
        self.collection_cards = {}
        self.collections_layout = None
        self.selected_collection = None
        
        # Track file data
        self.file_data_cache = {}

        self.stack = QStackedWidget()
        self.dashboard_widget = QWidget()
        
        # Auto-cleanup old recycle bin files on startup
        self.auto_cleanup_recycle_bin()
        
        self.init_ui()

        self.stack.addWidget(self.dashboard_widget)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stack)
        self.setLayout(main_layout)

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # ========== HEADER SECTION ==========
        header_layout = QHBoxLayout()
        
        menu_btn = create_menu_button(callback=lambda: print("Menu button clicked"))
        
        title = QLabel("My Documents")
        title.setStyleSheet("font-size: 24px; color: #084924; font-family: Poppins; font-weight:bold")
        
        # Search bar
        search_bar = QLineEdit()
        search_button = create_search_button(callback=lambda: print("Search button clicked"))
        search_bar.setPlaceholderText("Search my files...")
        search_bar.setMinimumWidth(300)
        search_bar.setStyleSheet("border-radius: 10px; padding: 5px; border: 2px solid #084924;")
        search_button.setMinimumWidth(55)
        search_button.setStyleSheet("border-radius: 10px; padding: 8px;")
        
        header_layout.addWidget(menu_btn)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(search_bar)
        header_layout.addWidget(search_button)
        
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(25)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        
        # ========== COLLECTIONS GRID ==========
        collections_scroll = QScrollArea()
        collections_scroll.setWidgetResizable(True)
        collections_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        collections_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        collections_scroll.setFixedHeight(200)
        collections_scroll.setStyleSheet("QScrollArea { border: none; }")
        collections_scroll.setGraphicsEffect(shadow)
        
        collections_container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(20, 15, 20, 15)
        
        # Header with buttons
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                border-bottom: 1px solid black;
                margin-bottom: 15px;
                padding-bottom: 10px;
            }
        """)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        collections_label = QLabel("Collections")
        collections_label.setStyleSheet("font-family: Poppins; font-size: 20px; padding: 5px;")
        collections_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        header_layout.addWidget(collections_label)
        header_layout.addStretch()
        header_widget.setLayout(header_layout)
        
        container_layout.addWidget(header_widget)
        
        # Collections grid
        self.collections_layout = QHBoxLayout()
        self.collections_layout.setSpacing(25)
        self.collections_layout.setContentsMargins(0, 0, 0, 0)
        
        # Load collections
        collections_data = self.controller.get_collections()
        for collection_data in collections_data:
            card = self.create_collection_card(
                collection_data['name'], 
                collection_data.get('icon', 'folder1.png'),
                file_count=len(collection_data.get('files', [])),
                collection_id=collection_data.get('id')
            )
            card.mousePressEvent = self.make_collection_single_click_handler(
                collection_data.get('id'), card
            )
            card.mouseDoubleClickEvent = self.make_collection_double_click_handler(
                collection_data.get('id')
            )
            self.collection_cards[collection_data.get('id')] = card
            self.collections_layout.addWidget(card)
        
        self.collections_layout.addStretch()
        container_layout.addLayout(self.collections_layout)
        collections_container.setLayout(container_layout)
        collections_scroll.setWidget(collections_container)
        main_layout.addWidget(collections_scroll)

        # ========== MAIN CONTENT AREA ==========
        content_layout = QHBoxLayout()

        # Files frame
        files_frame = QFrame()
        files_frame.setFrameShape(QFrame.Shape.Box)
        files_layout = QVBoxLayout()

        shadow2 = QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(20)
        shadow2.setOffset(0, 4)
        shadow2.setColor(QColor(0, 0, 0, 60))
        files_frame.setStyleSheet("border: none;")
        files_frame.setGraphicsEffect(shadow2)

        files_layout.addSpacing(10)

        # Files header
        files_header_layout = QHBoxLayout()
        files_layout.addSpacing(10)
        files_header_layout.setContentsMargins(0, 0, 0, 0)

        uploaded_files_label = QLabel("My Files (Latest 10)")
        uploaded_files_label.setStyleSheet("font-family: Poppins; font-size: 20px; padding: 5px;")
        uploaded_files_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        files_title = QPushButton("View All Files")
        files_title.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                border: none;
                border-bottom: 1.5px solid black;
                color: black;
                background-color: transparent;
            }
            QPushButton:hover {
                color: #555555;
            }
        """)
        files_title.clicked.connect(self.handle_view_uploaded_files)

        delete_btn = QPushButton("Deleted Files")
        delete_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                border: none;
                border-bottom: 1.5px solid black;
                color: black;
                background-color: transparent;
            }
            QPushButton:hover {
                color: #555555;
            }
        """)
        delete_btn.clicked.connect(self.handle_manage_deleted_files)
        
        # Approval requests button (faculty can also approve files)
        approval_btn = QPushButton("Approval Requests")
        approval_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                border: none;
                border-bottom: 1.5px solid black;
                color: black;
                background-color: transparent;
            }
            QPushButton:hover {
                color: #555555;
            }
        """)
        approval_btn.clicked.connect(self.handle_file_upload_requests)
        
        files_header_layout.addWidget(uploaded_files_label)
        files_header_layout.addStretch()
        files_header_layout.addWidget(approval_btn)
        files_header_layout.addWidget(files_title)
        files_header_layout.addWidget(delete_btn)
        files_layout.addLayout(files_header_layout)
        
        files_layout.addSpacing(10)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Plain)
        separator.setLineWidth(1)
        separator.setStyleSheet("""
            QFrame {
                background-color: black;
                color: black;
                border: none;
                max-height: 1.5px;
            }
        """)
        files_layout.addWidget(separator)
        files_layout.addSpacing(8)

        # Files table
        self.files_table = QTableView()
        self.files_model = QStandardItemModel(0, 5)
        self.files_model.setHorizontalHeaderLabels(["Filename", "Upload Date", "Type", "Category", "Status"])
        self.files_table.setModel(self.files_model)
        self.files_table.horizontalHeader().setStretchLastSection(True)
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.files_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.files_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.files_table.clicked.connect(self.handle_file_row_clicked)
        self.files_table.doubleClicked.connect(self.handle_file_row_double_clicked)
        self.files_table.setAlternatingRowColors(True)

        self.files_table.setStyleSheet("""
            QTableView {
                background-color: white;
                alternate-background-color: #d3d3d3;
                border: none;
                selection-background-color: #084924;
                color: black;
                gridline-color: transparent;
            }
            QHeaderView::section {
                background-color: #084924;
                color: white;
                font-weight: bold;
                border: none;
                padding: 8px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QTableCornerButton::section {
                background-color: #084924;
                border: none;
            }
            QTableView::item {
                border-bottom: 1px solid black;
                padding: 8px;
            }
        """)

        self.files_container_layout = files_layout
        # Load files
        self.refresh_files_table()
        
        # Store container layout reference
        files_layout.addWidget(self.files_table)
        files_frame.setLayout(files_layout)
        content_layout.addWidget(files_frame)

        main_layout.addLayout(content_layout)
        self.dashboard_widget.setLayout(main_layout)

    def create_collection_card(self, name, icon_filename="folder1.png", file_count=0, collection_id=None):
        """Creates a collection card widget"""
        card = QFrame()
        card.setObjectName("collection_card")
        if collection_id is not None:
            card.setProperty("collection_id", collection_id)
            card.setProperty("collection_name", name)
        card.setFrameShape(QFrame.Shape.Box)
        card.setFixedSize(90, 90)
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        card.setStyleSheet("""
            QFrame#collection_card {
                background-color: #084924;
                border: 1px solid #084924;
                border-radius: 8px;
            }
            QFrame#collection_card:hover {
                background-color: #064018;
                border: 2px solid #084924;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(2)
        
        from ...utils.icon_utils import IconLoader
        icon = IconLoader.create_icon_label(icon_filename, size=(32, 32), 
                                           alignment=Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("QLabel { background-color: transparent; color: #FDC601; }")
        
        label = QLabel(name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet("QLabel { background-color: transparent; color: white; font-weight: bold; }")
        
        count_label = QLabel(f"Files: {file_count}")
        count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_label.setStyleSheet("QLabel { background-color: transparent; color: #CCCCCC; font-size: 10px; }")
        count_label.setObjectName("file_count_label")
        
        layout.addWidget(icon)
        layout.addWidget(label)
        layout.addWidget(count_label)
        card.setLayout(layout)
        
        return card

    def add_file_to_table(self, name, date, ext, category, status):
        """Adds a file row to the table"""
        for row_idx in range(self.files_model.rowCount()):
            existing_name = self.files_model.item(row_idx, 0).text()
            if existing_name == name:
                return
        
        row = [
            QStandardItem(name), 
            QStandardItem(date), 
            QStandardItem(ext),
            QStandardItem(category),
            QStandardItem(status)
        ]
        self.files_model.appendRow(row)

    def handle_file_row_clicked(self, index):
        filename = self.files_model.item(index.row(), 0).text()
        print(f"File row clicked: {filename}")
    
    def handle_file_row_double_clicked(self, index):
        """Show file details dialog"""
        filename = self.files_model.item(index.row(), 0).text()
        self.show_file_details(filename)
    
    def show_file_details(self, filename):
        """Show file details dialog"""
        files_data = self.controller.get_files()
        file_data = None
        
        for f in files_data:
            if f['filename'] == filename:
                file_data = f
                break
        
        if file_data:
            from ...Shared.Dialogs.file_details_dialog import FileDetailsDialog
            dialog = FileDetailsDialog(
                self, 
                file_data=file_data, 
                controller=self.controller,
                is_deleted=False
            )
            dialog.file_updated.connect(self.on_file_updated_from_dialog)
            dialog.file_deleted.connect(self.on_file_deleted_from_dialog)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Error", f"Could not find details for '{filename}'")
    
    def on_file_updated_from_dialog(self, file_data):
        """Handle file updated signal"""
        print(f"File updated: {file_data}")
        self.refresh_files_table()
    
    def on_file_deleted_from_dialog(self, file_data):
        """Handle file deleted signal"""
        print(f"File deleted: {file_data}")
        self.refresh_files_table()
        self.refresh_all_collection_counts()

    def make_collection_single_click_handler(self, collection_id, card_widget):
        """Handle single click - select collection"""
        def handler(event):
            if self.selected_collection and self.selected_collection != card_widget:
                self.selected_collection.setStyleSheet("""
                    QFrame#collection_card {
                        background-color: #084924;
                        border: 1px solid #084924;
                        border-radius: 8px;
                    }
                    QFrame#collection_card:hover {
                        background-color: #064018;
                        border: 2px solid #084924;
                    }
                """)
            
            card_widget.setStyleSheet("""
                QFrame#collection_card {
                    background-color: #084924;
                    border: 2px solid #0078d4;
                    border-radius: 8px;
                }
                QFrame#collection_card:hover {
                    background-color: #064018;
                    border: 2px solid #0078d4;
                }
            """)
            self.selected_collection = card_widget
        return handler
    
    def make_collection_double_click_handler(self, collection_id):
        """Handle double click - open collection"""
        def handler(event):
            collection_name = self.controller._get_collection_name_by_id(collection_id)
            if not collection_name:
                print(f"Error: Collection ID {collection_id} not found")
                return
                
            print(f"Collection opened: {collection_name} (ID: {collection_id})")
            from ...Shared.Views.collection_view import CollectionView
            collection_view = CollectionView(
                self.username,
                self.roles,
                self.primary_role,
                self.token,
                collection_name=collection_name,
                stack=self.stack)

            collection_view.file_uploaded.connect(self.on_file_uploaded)
            collection_view.file_deleted.connect(self.on_file_deleted)
            collection_view.file_updated.connect(self.on_file_updated_from_dialog)

            self.stack.addWidget(collection_view)
            self.stack.setCurrentWidget(collection_view)
        return handler
    
    def on_file_uploaded(self, file_data):
        """Handle file uploaded event"""
        print(f"File uploaded: {file_data}")
        self.refresh_files_table()
        
        collection_id = file_data.get('collection_id')
        if collection_id is not None:
            self.update_collection_file_count(collection_id)
    
    def refresh_files_table(self):
        """Refresh the files table showing latest 10 files"""
        files_data = self.controller.get_files(limit=10)
        
        if len(files_data) == 0:
            self.files_table.setVisible(False)
            if not hasattr(self, 'files_empty_state') or not self.files_empty_state:
                self.files_empty_state = EmptyStateWidget(
                    icon_name="folder1.png",
                    title="No Files Yet",
                    message="Upload your first file to get started.",
                    action_text="Upload File"
                )
                self.files_empty_state.action_clicked.connect(self.handle_add_file)
                self.files_container_layout.addWidget(self.files_empty_state)
            else:
                self.files_empty_state.setVisible(True)
            return
        else:
            if hasattr(self, 'files_empty_state') and self.files_empty_state:
                self.files_empty_state.setVisible(False)
            self.files_table.setVisible(True)
        
        self.files_model.clear()
        self.file_data_cache.clear()
        self.files_model.setHorizontalHeaderLabels(['Filename', 'Upload Date', 'Type', 'Category', 'Status'])
        
        for idx, file_data in enumerate(files_data):
            approval_status = file_data.get('approval_status', 'approved')
            # Display all statuses using emoji map
            approval_map = {
                'pending': '🟡 Pending',
                'approved': '🟢 Approved',
                'accepted': '🟢 Accepted',
                'rejected': '🔴 Rejected'
            }
            status_display = approval_map.get(approval_status, '⚪ Unknown')
            
            self.add_file_to_table(
                file_data['filename'], 
                file_data.get('uploaded_date', file_data.get('time', 'N/A')), 
                file_data['extension'],
                file_data.get('category', 'None'),
                status_display
            )
            
            self.file_data_cache[file_data['filename']] = {
                'uploaded_date': file_data.get('uploaded_date', file_data.get('time', 'N/A')),
                'extension': file_data['extension'],
                'row_index': idx
            }
        
        print(f"Refreshed files table with {len(files_data)} files")
    
    def handle_manage_deleted_files(self):
        """Open deleted files view"""
        print("Manage Deleted Files clicked")
        from ...Shared.Views.deleted_files_view import DeletedFileView
        deleted_view = DeletedFileView(self.username, self.roles, self.primary_role, self.token, stack=self.stack)
        deleted_view.file_restored.connect(self.on_file_restored)
        self.stack.addWidget(deleted_view)
        self.stack.setCurrentWidget(deleted_view)
    
    def handle_view_uploaded_files(self):
        """Open uploaded files view"""
        print("View Uploaded Files clicked")
        from ...Shared.Views.uploaded_files_view import UploadedFilesView
        uploaded_view = UploadedFilesView(self.username, self.roles, self.primary_role, self.token, stack=self.stack)
        uploaded_view.file_deleted.connect(self.on_file_deleted)
        uploaded_view.file_uploaded.connect(self.on_file_uploaded)
        self.stack.addWidget(uploaded_view)
        self.stack.setCurrentWidget(uploaded_view)
    
    def handle_add_file(self):
        """Open file upload dialog"""
        print("Add file clicked")
        from ...Shared.Dialogs.file_upload_dialog import FileUploadDialog
        dialog = FileUploadDialog(self, username=self.username, role=self.primary_role)
        dialog.file_uploaded.connect(self.on_file_uploaded)
        dialog.exec()
    
    def on_file_deleted(self, file_data):
        """Handle file deleted event"""
        print(f"File deleted: {file_data}")
        self.refresh_files_table()
        self.refresh_all_collection_counts()
    
    def on_file_restored(self, file_data):
        """Handle file restored event"""
        print(f"File restored: {file_data}")
        self.refresh_files_table()
        self.refresh_all_collection_counts()
    
    def auto_cleanup_recycle_bin(self):
        """Auto cleanup old files from recycle bin"""
        try:
            success, message, count = self.controller.cleanup_old_recycle_bin_files(days=15)
            if success and count > 0:
                print(f"Auto-cleanup: {message}")
        except Exception as e:
            print(f"Error during auto-cleanup: {str(e)}")
    
    def update_collection_file_count(self, collection_id):
        """Update file count on collection card"""
        if collection_id not in self.collection_cards:
            return
        
        collection_data = self.controller._get_collection_by_id(collection_id)
        if not collection_data:
            return
        
        card = self.collection_cards[collection_id]
        count_label = card.findChild(QLabel, "file_count_label")
        
        if count_label:
            file_count = len(collection_data.get('files', []))
            count_label.setText(f"Files: {file_count}")
    
    def refresh_all_collection_counts(self):
        """Refresh all collection file counts"""
        collections_data = self.controller.get_collections()
        
        for collection_data in collections_data:
            collection_id = collection_data.get('id')
            
            if collection_id is not None and collection_id in self.collection_cards:
                card = self.collection_cards[collection_id]
                count_label = card.findChild(QLabel, "file_count_label")
                
                if count_label:
                    file_count = len(collection_data.get('files', []))
                    count_label.setText(f"Files: {file_count}")
    
    def handle_file_upload_requests(self):
        """Open the file upload approval view"""
        print("File Upload Requests clicked - Opening approval view")
        from ...Shared.Views.approval_view import ApprovalView
        approval_view = ApprovalView(
            self.username, 
            self.roles, 
            self.primary_role, 
            self.token,
            stack=self.stack
        )
        approval_view.file_approved.connect(self.on_file_approved)
        approval_view.file_rejected.connect(self.on_file_rejected)
        self.stack.addWidget(approval_view)
        self.stack.setCurrentWidget(approval_view)
    
    def on_file_approved(self, file_data):
        """Handle file approved event"""
        print(f"File approved: {file_data}")
        # Refresh files table to show updated approval status
        self.refresh_files_table()
        # Update collection counts if needed
        collection_id = file_data.get('collection_id')
        if collection_id is not None:
            self.update_collection_file_count(collection_id)
    
    def on_file_rejected(self, file_data):
        """Handle file rejected event"""
        print(f"File rejected: {file_data}")
        # Refresh files table to show updated approval status
        self.refresh_files_table()
