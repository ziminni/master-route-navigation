from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QHBoxLayout, QFrame, QLineEdit, QScrollArea,
                             QTableView, QHeaderView,
                             QSizePolicy, QStackedWidget, QMessageBox)
from PyQt6.QtGui import QFont, QStandardItemModel, QStandardItem, QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QRect
from ...controller.document_controller import DocumentController
from ...utils.icon_utils import create_menu_button, create_search_button, IconLoader
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor
from ...widgets.empty_state import EmptyStateWidget

from ...widgets.DonutWidget import DonutChartWidget


class AdminDash(QWidget):
    """
    Main Admin Dashboard Widget
    
    This widget displays a document management interface with:
    - Header with menu, title, and actions
    - Collections grid (horizontally scrollable)
    - Uploaded files list (scrollable table)
    - Storage usage chart
    
    Args: <This fields are necessary for the Router to recognize it as a widget>
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

        # Track collection widgets for efficient updates
        self.collection_cards = {}  # {collection_id: QFrame widget} - Keyed by ID for consistency
        self.collections_layout = None  # Reference to the layout
        self.selected_collection = None  # Track currently selected collection
        
        # Track file data for efficient updates
        self.file_data_cache = {}  # {'filename': {'time': ..., 'extension': ..., 'row_index': ...}}

        self.stack = QStackedWidget()

        self.dashboard_widget = QWidget()
        
        # Auto-cleanup old recycle bin files on startup
        self.auto_cleanup_recycle_bin()
        
        self.init_ui()

        self.stack.addWidget(self.dashboard_widget)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stack)
        self.setLayout(main_layout)
        
        # self.refresh_storage_chart() #for testing only

        

    def init_ui(self):
        
        main_layout = QVBoxLayout()
        # ========== HEADER SECTION ==========
        header_layout = QHBoxLayout()
        
        
        
        # Menu button with hamburger icon - using utility
        menu_btn = create_menu_button(callback=lambda: print("Menu button clicked"))
        
        title = QLabel("Documents")
        title.setStyleSheet("font-size: 24px; color: #084924; font-family: Poppins; font-weight:bold")
            
        # Changed from QLabel to QLineEdit for text input
        search_bar = QLineEdit()
        search_button = create_search_button(callback=lambda: print("Search button clicked"))
        search_bar.setPlaceholderText("Search collections or files...")
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
        main_layout.addSpacing(25)  # Adjust spacing as desired (10–20 looks good)


        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))  # semi-transparent black
        # ========== COLLECTIONS GRID ==========
        collections_scroll = QScrollArea()
        
        collections_scroll.setWidgetResizable(True)
        collections_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        collections_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        collections_scroll.setFixedHeight(200)  # Increased height to accommodate header and buttons
        collections_scroll.setStyleSheet("QScrollArea { border: none; }")
        collections_scroll.setGraphicsEffect(shadow)
        
        
        collections_container = QWidget()
        # collections_container.setStyleSheet("QWidget { background-color: white; }")
        
        
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(20, 15, 20, 15)  # Add padding around the edges
        
        # Add header with buttons and underline
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
        
        # Collections label
        collections_label = QLabel("Collections")
        collections_label.setStyleSheet("font-family: Poppins; font-size: 20px; padding: 5px;")
        collections_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Align vertically with buttons
        
        # Action buttons
        add_collection_btn = QPushButton("Add Collection")
        add_collection_btn.clicked.connect(self.handle_add_collection)
        add_collection_btn.setStyleSheet("""
    QPushButton {
        border: none;
        font-family: Poppins;
        padding: 5px;
        font-weight: bold;
        text-decoration: underline;
        color: #000000;
    }
    QPushButton:hover {
        color: #555555; /* lighter text (and underline) when hovered */
    }
""")
        
        delete_collection_btn = QPushButton("Delete Collection")
        delete_collection_btn.clicked.connect(self.handle_delete_collection)
        delete_collection_btn.setStyleSheet("""
    QPushButton {
        border: none;
        font-family: Poppins;
        padding: 5px;
        font-weight: bold;
        text-decoration: underline;
        color: #000000;
    }
    QPushButton:hover {
        color: #555555; /* lighter text (and underline) when hovered */
    }
""")
        
        upload_link = QPushButton("File Upload Requests")
        upload_link.clicked.connect(lambda: print("File Upload Requests clicked"))
        upload_link.setStyleSheet("""
    QPushButton {
        border: none;
        font-family: Poppins;
        padding: 5px;
        font-weight: bold;
        text-decoration: underline;
        color: #000000;
    }
    QPushButton:hover {
        color: #555555; /* lighter text (and underline) when hovered */
    }
""")
        
        header_layout.addWidget(collections_label)
        header_layout.addStretch()
        header_layout.addWidget(add_collection_btn)
        header_layout.addWidget(delete_collection_btn)
        header_layout.addWidget(upload_link)
        header_widget.setLayout(header_layout)
        
        container_layout.addWidget(header_widget)
        
        
        # Collections grid
        self.collections_layout = QHBoxLayout()  # Store as instance variable
        self.collections_layout.setSpacing(25)
        self.collections_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins from the collections layout
        
        # Load collections using controller and track them
        collections_data = self.controller.get_collections()
        for collection_data in collections_data:
            collection_id = collection_data.get('id')
            collection_name = collection_data['name']
            file_count = len(collection_data.get('files', []))  # Count files in collection
            collection = self.create_collection_card(
                collection_name, 
                collection_data.get('icon', 'folder1.png'),
                file_count=file_count,
                collection_id=collection_id  # Pass collection_id to card
            )
            # Set up single click and double click handlers (now using collection_id)
            collection.mousePressEvent = self.make_collection_single_click_handler(collection_id, collection)
            collection.mouseDoubleClickEvent = self.make_collection_double_click_handler(collection_id)
            self.collection_cards[collection_id] = collection  # Track widget by ID
            self.collections_layout.addWidget(collection)
        
        self.collections_layout.addStretch()
        
        # Add the collections layout to the container
        container_layout.addLayout(self.collections_layout)
        collections_container.setLayout(container_layout)
        
        # Set the container as the scroll area's widget
        collections_scroll.setWidget(collections_container)
        main_layout.addWidget(collections_scroll)

        # ========== MAIN CONTENT AREA ==========
        content_layout = QHBoxLayout()

        # --- LEFT SIDE ---
        files_frame = QFrame()
        files_frame.setFrameShape(QFrame.Shape.Box)
        files_layout = QVBoxLayout()

        shadow2 = QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(20)
        shadow2.setOffset(0, 4)
        shadow2.setColor(QColor(0, 0, 0, 60))
        files_frame.setStyleSheet("border: none;")
        files_frame.setGraphicsEffect(shadow2)

        # Add space above "Uploaded Files"
        files_layout.addSpacing(10)

        # Files header - now a clickable button
        files_header_layout = QHBoxLayout()
        files_layout.addSpacing(10)
        
        files_header_layout.setContentsMargins(0, 0, 0, 0)

        
        uploaded_files_label = QLabel("Uploaded Files")
        uploaded_files_label.setStyleSheet("font-family: Poppins; font-size: 20px; padding: 5px;")
        uploaded_files_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Align vertically with buttons
        

        files_title = QPushButton("Manage Uploaded Files")
        files_title.setStyleSheet("""
    QPushButton {
        font-weight: bold;
        border: none;
        border-bottom: 1.5px solid black;  /* bold underline */
        color: black;
        background-color: transparent;
    }
    QPushButton:hover {
        color: #555555; /* lighter text (and underline) when hovered */
    }
""")
        files_title.clicked.connect(self.handle_view_uploaded_files)

        delete_btn = QPushButton("Manage Deleted Files")
        delete_btn.setStyleSheet("""
    QPushButton {
        font-weight: bold;
        border: none;
        border-bottom: 1.5px solid black;  /* bold underline */
        color: black;
        background-color: transparent;
    }
    QPushButton:hover {
        color: #555555; /* lighter text (and underline) when hovered */
    }
""")
        delete_btn.clicked.connect(self.handle_manage_deleted_files)
        
        
        files_header_layout.addWidget(uploaded_files_label)
        files_header_layout.addStretch()
        files_header_layout.addWidget(files_title)
        files_header_layout.addWidget(delete_btn)
        files_layout.addLayout(files_header_layout)
        
        files_layout.addSpacing(10)


        # Add horizontal separator line
        # Add horizontal separator line (thin black)
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



        # Create a table view and model for files
        self.files_table = QTableView()
        self.files_model = QStandardItemModel(0, 5)
        self.files_model.setHorizontalHeaderLabels(["Filename", "Upload Date", "Type", "Status", "Approval"])
        self.files_table.setModel(self.files_model)
        self.files_table.horizontalHeader().setStretchLastSection(True)
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.files_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.files_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.files_table.clicked.connect(self.handle_file_row_clicked)
        self.files_table.doubleClicked.connect(self.handle_file_row_double_clicked)
        self.files_table.setAlternatingRowColors(True)

        

        # Style the table header
        self.files_table.setStyleSheet("""
    QTableView {
        background-color: white;
        alternate-background-color: #d3d3d3; /* light grey for alternating rows */
        border: none;
        selection-background-color: #084924; /* dark green highlight */
        color: black;
        gridline-color: transparent;
    }
    QHeaderView::section {
        background-color: #084924; /* dark green header */
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
        border-bottom: 1px solid black; /* thin black separator line */
        padding: 8px;
    }
""")

        # Connect model signals for automatic cache consistency
        self.files_model.rowsRemoved.connect(self._on_rows_removed)
        self.files_model.dataChanged.connect(self._on_data_changed)

        # Create container for table and empty state
        self.files_container = QWidget()
        self.files_container_layout = QVBoxLayout(self.files_container)
        self.files_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Load file data using controller
        files_data = self.controller.get_files()

        # Show empty state or populate table
        if len(files_data) == 0:
            # Show empty state
            self.files_empty_state = EmptyStateWidget(
                icon_name="folder1.png",
                title="No Files Yet",
                message="Upload your first file to get started with document management.",
                action_text="Upload File"
            )
            self.files_empty_state.action_clicked.connect(self.handle_add_file)
            self.files_container_layout.addWidget(self.files_empty_state)
            self.files_table.setVisible(False)
        else:
            # Populate and track files
            for idx, file_data in enumerate(files_data):
                status = file_data.get('status', 'available')
                approval = file_data.get('approval_status', 'pending')
                self.add_file_to_table(
                    file_data['filename'], 
                    file_data.get('uploaded_date', file_data.get('time', 'N/A')), 
                    file_data['extension'],
                    status,
                    approval
                )
                # Track file data in cache
                self.file_data_cache[file_data['filename']] = {
                    'uploaded_date': file_data.get('uploaded_date', file_data.get('time', 'N/A')),
                    'extension': file_data['extension'],
                    'status': status,
                    'approval_status': approval,
                    'row_index': idx
                }
            self.files_table.setVisible(True)
        
        self.files_container_layout.addWidget(self.files_table)
        files_layout.addWidget(self.files_container)

        # Populate and track files
        for idx, file_data in enumerate(files_data):
            status = file_data.get('status', 'available')
            approval = file_data.get('approval_status', 'pending')
            self.add_file_to_table(
                file_data['filename'], 
                file_data.get('uploaded_date', file_data.get('time', 'N/A')), 
                file_data['extension'],
                status,
                approval
            )
            # Track file data in cache
            self.file_data_cache[file_data['filename']] = {
                'uploaded_date': file_data.get('uploaded_date', file_data.get('time', 'N/A')),
                'extension': file_data['extension'],
                'status': status,
                'approval_status': approval,
                'row_index': idx
            }
        files_layout.addWidget(self.files_table)
        
        # New button at bottom right
        new_btn = QPushButton("+  New")
        new_btn.setStyleSheet("color: #084924; border-radius: 5px; width: 70px; height: 25px; border: 1px solid #084924; font-family: Poppins; font-weight: bold")
        new_btn.clicked.connect(self.handle_add_file)

        new_btn_layout = QHBoxLayout()
        new_btn_layout.addStretch()
        new_btn_layout.addWidget(new_btn)
        files_layout.addLayout(new_btn_layout)
        
        files_frame.setLayout(files_layout)
        content_layout.addWidget(files_frame, 6)

        chart_frame = QFrame()
        chart_frame.setFrameShape(QFrame.Shape.Box)
        chart_layout = QVBoxLayout()
        
        # Load storage data using controller
        storage_data = self.controller.get_storage_info()
        
        
        shadow1 = QGraphicsDropShadowEffect()
        shadow1.setBlurRadius(20)
        shadow1.setOffset(0, 4)
        shadow1.setColor(QColor(0, 0, 0, 60)) 
        # Create actual donut chart widget
        self.donut_chart = DonutChartWidget(
            used_percentage=storage_data['usage_percentage'],
            used_gb=storage_data['used_size_gb'],
            total_gb=storage_data['total_size_gb']
        )
        self.donut_chart.setMinimumHeight(250)
        chart_layout.addWidget(self.donut_chart)
        
        chart_frame.setStyleSheet("border: none")
        chart_frame.setGraphicsEffect(shadow1)
    
            
        legend_layout = QVBoxLayout()
        
        used_row = QHBoxLayout()
        used_row.setContentsMargins(25, 0, 25, 0)  # add left & right spacing

        used_color = QLabel("●") 
        used_color.setStyleSheet("color: #084924; font-size: 24px; font-weight: bold; font-family: Poppins;")  # green dot

        used_label = QLabel("Used Storage")
        used_label.setStyleSheet("font-family: Poppins; font-size: 14px;")

        used_size = QLabel(f"Actual Size: {storage_data['used_size_gb']} GB")
        used_size.setStyleSheet("font-family: Poppins; font-size: 14px;")

        used_row.addWidget(used_color)
        used_row.addWidget(used_label)
        used_row.addStretch()
        used_row.addWidget(used_size)


        free_row = QHBoxLayout()
        free_row.setContentsMargins(25, 0, 25, 0)  # add left & right spacing

        free_color = QLabel("●")
        free_color.setStyleSheet("color: #E0E0E0; font-size: 24px; font-weight: bold; font-family: Poppins;")  # light gray dot

        free_label = QLabel("Free Space")
        free_label.setStyleSheet("font-family: Poppins; font-size: 14px;")

        free_size = QLabel(f"Unused Size: {storage_data['free_size_gb']} GB")
        free_size.setStyleSheet("font-family: Poppins; font-size: 14px;")

        free_row.addWidget(free_color)
        free_row.addWidget(free_label)
        free_row.addStretch()
        free_row.addWidget(free_size)
                
        
        legend_layout.addLayout(used_row)
        legend_layout.addLayout(free_row)
        
        chart_layout.addLayout(legend_layout)
        chart_frame.setLayout(chart_layout)
        content_layout.addWidget(chart_frame, 4)  # Takes 40% of width

        # Add content section to main layout
        main_layout.addLayout(content_layout)

        # Set the main layout for this widget
        self.dashboard_widget.setLayout(main_layout)

    def create_collection_card(self, name, icon_filename="folder1.png", file_count=0, collection_id=None):
        """
        Creates a single collection card widget
        
        Args:
            name (str): Display name for the collection
            icon_filename (str): Icon filename from Assets folder (default: "folder.png")
            file_count (int): Number of files in the collection
            collection_id (int): Unique collection ID for identification
            
        Returns:
            QFrame: A frame containing the collection card UI
        """
        card = QFrame()
        card.setObjectName("collection_card")  # Set object name for targeted styling
        # Store collection_id in the widget for later retrieval
        if collection_id is not None:
            card.setProperty("collection_id", collection_id)
            card.setProperty("collection_name", name)  # Also store name for display
        card.setFrameShape(QFrame.Shape.Box)
        card.setFixedSize(90, 90)
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Set green background for collections loaded from database
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
            QFrame#collection_card:pressed {
                background-color: #084924;
                border: 2px solid #0078d4;
            }
        """)
        
        # Vertical layout: icon stacked on top of label
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(2)  # Reduce spacing between elements
        
        # Load icon using IconLoader with yellow color filter
        icon = IconLoader.create_icon_label(icon_filename, size=(32, 32), alignment=Qt.AlignmentFlag.AlignCenter)
        # Apply yellow color to the icon
        icon.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #FDC601;
            }
        """)
        
        label = QLabel(name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)  # Allow text wrapping if name is long
        label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: white;
                font-weight: bold;
            }
        """)
        
        # File count indicator
        count_label = QLabel(f"Files: {file_count}")
        count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #CCCCCC;
                font-size: 10px;
            }
        """)
        count_label.setObjectName("file_count_label")  # Give it a unique name to find it later
        
        layout.addWidget(icon)
        layout.addWidget(label)
        layout.addWidget(count_label)
        card.setLayout(layout)
        
        return card

    def add_file_to_table(self, name, date, ext, status, approval):
        """
        Adds a file row to the files table (QTableView/QStandardItemModel)
        Args:
            name (str): Filename
            date (str): Upload date
            ext (str): File extension
            status (str): File status (available, soft_deleted, permanently_deleted)
            approval (str): Approval status (pending, accepted, rejected)
        """
        # CRITICAL: Check if file already exists in the model to prevent duplicates
        for row_idx in range(self.files_model.rowCount()):
            existing_name = self.files_model.item(row_idx, 0).text()
            if existing_name == name:
                print(f"WARNING: File '{name}' already exists in table at row {row_idx}, skipping duplicate add")
                return
        
        # Get emoji indicators
        status_emoji = self._get_status_emoji(status)
        approval_emoji = self._get_approval_emoji(approval)
        
        row = [
            QStandardItem(name), 
            QStandardItem(date), 
            QStandardItem(ext),
            QStandardItem(status_emoji),
            QStandardItem(approval_emoji)
        ]
        self.files_model.appendRow(row)

    def handle_file_row_clicked(self, index):
            # Get filename from the model
            filename = self.files_model.item(index.row(), 0).text()
            print(f"File row clicked: {filename}")
    
    def handle_file_row_double_clicked(self, index):
        """Handle file row double-click - show file details dialog"""
        filename = self.files_model.item(index.row(), 0).text()
        self.show_file_details(filename)
    
    def show_file_details(self, filename):
        """Show file details dialog using custom widget"""
        # Get file details from uploaded files
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
        """Handle file updated signal from details dialog"""
        print(f"File updated from dialog: {file_data}")
        # Refresh files table to show updated data
        self.refresh_files_table()
    
    def on_file_deleted_from_dialog(self, file_data):
        """Handle file deleted signal from details dialog"""
        print(f"File deleted from dialog: {file_data}")
        # Refresh files table
        self.refresh_files_table()
        
        # Update collection file counts
        print(f"DEBUG: file_data keys from dialog delete: {file_data.keys()}")
        collection_name = file_data.get('collection_name') or file_data.get('category')
        if collection_name:
            print(f"DEBUG: Updating specific collection: {collection_name}")
            self.update_collection_file_count(collection_name)
        else:
            print(f"DEBUG: No collection info, refreshing all collection counts")
            # If we can't determine which collection, refresh all
            self.refresh_all_collection_counts()

    def deleted_click_handler(self, event):
        def handler(event):
            print("Deleted Files clicked")
            from ...Shared.Views.deleted_files_view import DeletedFileView
            deleted_file_view = DeletedFileView(self.username, self.roles, self.primary_role, self.token, stack=self.stack)
            self.stack.addWidget(deleted_file_view)
            self.stack.setCurrentWidget(deleted_file_view)
        return handler
    
    def make_collection_single_click_handler(self, collection_id, card_widget):
        """Handle single click on collection - highlight/select it"""
        def handler(event):
            collection_name = card_widget.property("collection_name")
            print(f"Collection selected: {collection_name} (ID: {collection_id})")
            # Clear previous selection - restore original green styling
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
            
            # Highlight current selection with blue border but keep green background
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
        """Handle double click on collection - open it"""
        def handler(event):
            # Get collection name from ID for display
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
                collection_name=collection_name,  # Still pass name for now (collection_view needs refactoring too)
                stack=self.stack)

            # Connect all signals from collection view
            collection_view.file_uploaded.connect(self.on_file_uploaded)
            collection_view.file_deleted.connect(self.on_file_deleted)
            collection_view.file_updated.connect(self.on_file_updated_from_dialog)

            self.stack.addWidget(collection_view)
            self.stack.setCurrentWidget(collection_view)
        return handler
    
    def make_collection_click_handler(self, name):
        """Deprecated - kept for backward compatibility"""
        return self.make_collection_double_click_handler(name)

    def handle_add_collection(self):
        """Open the add collection dialog popup"""
        print("Add Collection clicked - Opening dialog")
        from ...Shared.Dialogs.add_collection_dialog import AddCollectionDialog
        dialog = AddCollectionDialog(self)
        dialog.collection_created.connect(self.on_collection_created)
        dialog.exec()  # Show modal dialog
    
    def handle_delete_collection(self):
        """Delete the currently selected collection"""
        if not self.selected_collection:
            QMessageBox.warning(
                self, 
                "No Selection", 
                "Please select a collection first by clicking on it."
            )
            return
        
        # Get the collection ID from the selected widget
        collection_id = self.selected_collection.property("collection_id")
        collection_name = self.selected_collection.property("collection_name")
        
        if collection_id is None or not collection_name:
            QMessageBox.warning(self, "Error", "Could not identify the selected collection.")
            return
        
        # Check if collection is empty before showing confirmation
        is_empty, file_count = self.controller.is_collection_empty(collection_id)
        
        if file_count == -1:
            QMessageBox.warning(self, "Error", f"Collection '{collection_name}' not found.")
            return
        
        if not is_empty:
            QMessageBox.warning(
                self,
                "Cannot Delete Collection",
                f"The collection '{collection_name}' contains {file_count} file(s).\n\n"
                f"Please remove all files from this collection before deleting it.\n\n"
                f"You can move files to another collection or delete them individually.",
            )
            return
        
        # Confirmation dialog (only shown if collection is empty)
        reply = QMessageBox.question(
            self,
            'Confirm Delete Collection',
            f"Are you sure you want to delete the empty collection '{collection_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Delete collection using controller
            success, message = self.controller.delete_collection(collection_id)
            
            if success:
                QMessageBox.information(self, "Success", message)
                
                # Remove the collection card from UI
                self.collections_layout.removeWidget(self.selected_collection)
                self.selected_collection.deleteLater()  # Schedule for deletion
                
                # Remove from tracking dictionary (using ID as key)
                del self.collection_cards[collection_id]
                
                # Clear selection
                self.selected_collection = None
                
                print(f"Collection '{collection_name}' (ID: {collection_id}) deleted successfully")
            else:
                QMessageBox.critical(self, "Error", f"Failed to delete collection: {message}")
    
    def handle_add_file(self):
        """Open the file upload dialog popup"""
        print("Add file clicked - Opening dialog")
        from ...Shared.Dialogs.file_upload_dialog import FileUploadDialog
        dialog = FileUploadDialog(self, username=self.username, role=self.primary_role)
        dialog.file_uploaded.connect(self.on_file_uploaded)
        dialog.exec()
    
    def on_collection_created(self, collection_data):
        """Handle collection created event - incremental update"""
        print(f"Collection created: {collection_data}")
        
        collection_id = collection_data.get('id')
        collection_name = collection_data.get('name')
        
        if collection_id is None or not collection_name:
            # Fallback to full refresh if ID or name not provided
            self.refresh_collections()
            return
        
        # Check if collection already exists (avoid duplicates)
        if collection_id in self.collection_cards:
            print(f"Collection '{collection_name}' (ID: {collection_id}) already exists, skipping.")
            return

        # Add single collection instead of full refresh
        file_count = len(collection_data.get('files', []))
        card = self.create_collection_card(
            collection_name, 
            collection_data.get('icon', 'folder1.png'),
            file_count=file_count,
            collection_id=collection_id
        )
        # Set up single click and double click handlers
        card.mousePressEvent = self.make_collection_single_click_handler(collection_id, card)
        card.mouseDoubleClickEvent = self.make_collection_double_click_handler(collection_id)
        self.collection_cards[collection_id] = card
        
        # Insert before the stretch (which is at the last position)
        insert_position = self.collections_layout.count() - 1
        self.collections_layout.insertWidget(insert_position, card)
        print(f"Added new collection to UI: {collection_name} (ID: {collection_id})")
    
    def on_file_uploaded(self, file_data):
        """Handle file uploaded event - incremental update"""
        print(f"File uploaded: {file_data}")
        
        filename = file_data.get('filename')
        if not filename:
            # Fallback to full refresh if filename not provided
            self.refresh_files_table()
            return
        
        # CRITICAL FIX: Handle empty state transition
        # If table is hidden (empty state showing), we need to show it
        if not self.files_table.isVisible():
            print("Transitioning from empty state to populated files table")
            if hasattr(self, 'files_empty_state') and self.files_empty_state:
                self.files_empty_state.setVisible(False)
            self.files_table.setVisible(True)
        
        # Check if file already exists
        if filename in self.file_data_cache:
            # Update existing file data
            row_idx = self.file_data_cache[filename]['row_index']
            status = file_data.get('status', 'available')
            approval = file_data.get('approval_status', 'pending')
            
            self.files_model.item(row_idx, 0).setText(file_data.get('filename', filename))
            self.files_model.item(row_idx, 1).setText(file_data.get('uploaded_date', file_data.get('time', '')))
            self.files_model.item(row_idx, 2).setText(file_data.get('extension', ''))
            self.files_model.item(row_idx, 3).setText(self._get_status_emoji(status))
            self.files_model.item(row_idx, 4).setText(self._get_approval_emoji(approval))
            
            # Update cache
            self.file_data_cache[filename]['uploaded_date'] = file_data.get('uploaded_date', file_data.get('time', ''))
            self.file_data_cache[filename]['extension'] = file_data.get('extension', '')
            self.file_data_cache[filename]['status'] = status
            self.file_data_cache[filename]['approval_status'] = approval
            print(f"Updated existing file in UI: {filename}")
        else:
            # Add new file
            status = file_data.get('status', 'available')
            approval = file_data.get('approval_status', 'pending')
            
            self.add_file_to_table(
                file_data.get('filename', ''),
                file_data.get('uploaded_date', file_data.get('time', '')),
                file_data.get('extension', ''),
                status,
                approval
            )
            
            # Add to cache
            self.file_data_cache[filename] = {
                'uploaded_date': file_data.get('uploaded_date', file_data.get('time', '')),
                'extension': file_data.get('extension', ''),
                'status': status,
                'approval_status': approval,
                'row_index': self.files_model.rowCount() - 1
            }
            print(f"Added new file to UI: {filename}")
        
        # Update collection file count if file was added to a collection
        print(f"DEBUG: file_data keys: {file_data.keys()}")
        print(f"DEBUG: collection_id = {file_data.get('collection_id')}")

        collection_id = file_data.get('collection_id')
        if collection_id is not None:
            print(f"DEBUG: Updating count for collection ID: {collection_id}")
            self.update_collection_file_count(collection_id)
        else:
            print(f"DEBUG: No collection_id found in file_data")
    
    def refresh_collections(self):
        """Efficiently refresh the collections grid with incremental updates"""
        if not self.collections_layout:
            return
        
        # Get fresh data from controller
        collections_data = self.controller.get_collections()
        fresh_collection_ids = {col['id'] for col in collections_data}
        current_collection_ids = set(self.collection_cards.keys())
        
        # Identify changes (by ID)
        removed_collection_ids = current_collection_ids - fresh_collection_ids
        new_collections = [col for col in collections_data if col['id'] not in current_collection_ids]
        
        # Remove deleted collections
        for removed_id in removed_collection_ids:
            widget = self.collection_cards.pop(removed_id)
            removed_name = widget.property("collection_name")
            self.collections_layout.removeWidget(widget)
            widget.deleteLater()
            print(f"Removed collection: {removed_name} (ID: {removed_id})")
        
        # Add new collections (insert before the stretch item)
        for new_collection_data in new_collections:
            collection_id = new_collection_data['id']
            collection_name = new_collection_data['name']
            file_count = len(new_collection_data.get('files', []))
            
            card = self.create_collection_card(
                collection_name, 
                new_collection_data.get('icon', 'folder1.png'),
                file_count=file_count,
                collection_id=collection_id
            )
            card.mousePressEvent = self.make_collection_single_click_handler(collection_id, card)
            card.mouseDoubleClickEvent = self.make_collection_double_click_handler(collection_id)
            self.collection_cards[collection_id] = card
            
            # Insert before the stretch (which is at the last position)
            insert_position = self.collections_layout.count() - 1
            self.collections_layout.insertWidget(insert_position, card)
            print(f"Added collection: {collection_name} (ID: {collection_id})")
    
    def refresh_files_table(self):
        """Efficiently refresh the uploaded files table with incremental updates"""
        # Get fresh data from controller
        files_data = self.controller.get_files()
        fresh_files = {f['filename']: f for f in files_data}
        
        # Handle empty state
        if len(files_data) == 0:
            self.files_table.setVisible(False)
            if not hasattr(self, 'files_empty_state') or not self.files_empty_state:
                self.files_empty_state = EmptyStateWidget(
                    icon_name="document.png",
                    title="No Files Yet",
                    message="Upload your first file to get started with document management.",
                    action_text="Upload File"
                )
                self.files_empty_state.action_clicked.connect(self.handle_add_file)
                self.files_container_layout.addWidget(self.files_empty_state)
            else:
                self.files_empty_state.setVisible(True)
            return
        else:
            # Hide empty state and show table
            if hasattr(self, 'files_empty_state') and self.files_empty_state:
                self.files_empty_state.setVisible(False)
            self.files_table.setVisible(True)
        
        current_filenames = set(self.file_data_cache.keys())
        fresh_filenames = set(fresh_files.keys())
        
        # Identify changes
        removed_files = current_filenames - fresh_filenames
        new_files = fresh_filenames - current_filenames
        existing_files = current_filenames & fresh_filenames
        
        # Check for modified files (data changed but file still exists)
        modified_files = set()
        for filename in existing_files:
            cached = self.file_data_cache[filename]
            fresh = fresh_files[filename]
            if (cached.get('uploaded_date') != fresh.get('uploaded_date', fresh.get('time', '')) or 
                cached.get('extension') != fresh.get('extension') or
                cached.get('status') != fresh.get('status', 'available') or
                cached.get('approval_status') != fresh.get('approval_status', 'pending')):
                modified_files.add(filename)
        
        # Remove deleted files (sort by row index descending to avoid index shifting issues)
        for filename in sorted(removed_files, 
                              key=lambda f: self.file_data_cache[f]['row_index'], 
                              reverse=True):
            row_idx = self.file_data_cache[filename]['row_index']
            self.files_model.removeRow(row_idx)
            del self.file_data_cache[filename]
            print(f"Removed file: {filename}")
        
        # Update modified files
        for filename in modified_files:
            row_idx = self.file_data_cache[filename]['row_index']
            fresh = fresh_files[filename]
            status = fresh.get('status', 'available')
            approval = fresh.get('approval_status', 'pending')
            
            self.files_model.item(row_idx, 0).setText(fresh['filename'])
            self.files_model.item(row_idx, 1).setText(fresh.get('uploaded_date', fresh.get('time', '')))
            self.files_model.item(row_idx, 2).setText(fresh['extension'])
            self.files_model.item(row_idx, 3).setText(self._get_status_emoji(status))
            self.files_model.item(row_idx, 4).setText(self._get_approval_emoji(approval))
            
            # Update cache
            self.file_data_cache[filename]['uploaded_date'] = fresh.get('uploaded_date', fresh.get('time', ''))
            self.file_data_cache[filename]['extension'] = fresh['extension']
            self.file_data_cache[filename]['status'] = status
            self.file_data_cache[filename]['approval_status'] = approval
            print(f"Updated file: {filename}")
        
        # Add new files
        for filename in new_files:
            fresh = fresh_files[filename]
            status = fresh.get('status', 'available')
            approval = fresh.get('approval_status', 'pending')
            
            self.add_file_to_table(
                fresh['filename'], 
                fresh.get('uploaded_date', fresh.get('time', '')), 
                fresh['extension'],
                status,
                approval
            )
            
            # Add to cache with current row index
            self.file_data_cache[filename] = {
                'uploaded_date': fresh.get('uploaded_date', fresh.get('time', '')),
                'extension': fresh['extension'],
                'status': status,
                'approval_status': approval,
                'row_index': self.files_model.rowCount() - 1
            }
            print(f"Added file: {filename}")
        
        # Rebuild row indices after all changes (removals shift indices)
        if removed_files:
            self._rebuild_file_indices()
    
    def handle_manage_deleted_files(self):
        print("Manage Deleted Files clicked")
        from ...Shared.Views.deleted_files_view import DeletedFileView
        deleted_view = DeletedFileView(self.username, self.roles, self.primary_role, self.token, stack=self.stack)
        deleted_view.file_restored.connect(self.on_file_restored)
        self.stack.addWidget(deleted_view)
        self.stack.setCurrentWidget(deleted_view)
    
    def handle_view_uploaded_files(self):
        """Open the uploaded files view"""
        print("View Uploaded Files clicked")
        from ...Shared.Views.uploaded_files_view import UploadedFilesView
        uploaded_view = UploadedFilesView(self.username, self.roles, self.primary_role, self.token, stack=self.stack)
        uploaded_view.file_deleted.connect(self.on_file_deleted)
        uploaded_view.file_uploaded.connect(self.on_file_uploaded)
        self.stack.addWidget(uploaded_view)
        self.stack.setCurrentWidget(uploaded_view)
    
    def on_file_deleted(self, file_data):
        """Handle file deleted event - refresh the files table and update collection count"""
        print(f"File deleted: {file_data}")
        self.refresh_files_table()
        
        # Update collection file count if file was deleted from a collection
        print(f"DEBUG: file_data keys on delete: {file_data.keys()}")
        print(f"DEBUG: collection_id = {file_data.get('collection_id')}")
        
        # The file's original collections are stored in _original_collections (array of IDs)
        original_collections = file_data.get('_original_collections', [])
        if original_collections:
            print(f"DEBUG: Updating counts for collections (IDs): {original_collections}")
            for collection_id in original_collections:
                print(f"DEBUG: Updating count for collection ID after deletion: {collection_id}")
                self.update_collection_file_count(collection_id)
        else:
            print(f"DEBUG: No original_collections found in deleted file_data, updating all collections")
            # If we can't determine which collections, refresh all collection counts
            self.refresh_all_collection_counts()
    
    def on_file_restored(self, file_data):
        """Handle file restored event - refresh the files table and update collection counts"""
        print(f"File restored: {file_data}")
        self.refresh_files_table()
        
        # Update collection file counts - file was restored back to its original collections
        print(f"DEBUG: file_data keys on restore: {file_data.keys()}")
        print(f"DEBUG: _original_collections = {file_data.get('_original_collections')}")
        
        # Check for original collections (stored during deletion as collection IDs)
        original_collections = file_data.get('_original_collections', [])
        if original_collections:
            print(f"DEBUG: Updating counts for restored collections (IDs): {original_collections}")
            # _original_collections stores collection IDs (integers)
            # Now that update_collection_file_count uses IDs, we can pass them directly
            for collection_id in original_collections:
                print(f"DEBUG: Updating count for collection ID: {collection_id}")
                self.update_collection_file_count(collection_id)
        else:
            print(f"DEBUG: No original collections found, refreshing all collection counts")
            self.refresh_all_collection_counts()
    
    def auto_cleanup_recycle_bin(self):
        """Automatically cleanup old files from recycle bin on startup"""
        try:
            print("DEBUG: Starting auto-cleanup on startup...")
            success, message, count = self.controller.cleanup_old_recycle_bin_files(days=15)
            if success and count > 0:
                print(f"Auto-cleanup: {message}")
                print(f"WARNING: {count} files were auto-deleted on startup!")
            elif not success:
                print(f"Auto-cleanup failed: {message}")
            else:
                print("DEBUG: Auto-cleanup completed, no files deleted")
        except Exception as e:
            print(f"Error during auto-cleanup: {str(e)}")
    
    def _rebuild_file_indices(self):
        """
        Rebuild row indices in file_data_cache after removals.
        This ensures cache indices match actual model row positions.
        """
        # Iterate through model rows and update cache with correct indices
        for row_idx in range(self.files_model.rowCount()):
            filename = self.files_model.item(row_idx, 0).text()
            if filename in self.file_data_cache:
                self.file_data_cache[filename]['row_index'] = row_idx
    
    def _on_rows_removed(self, parent, first, last):
        """
        Auto-update cache when rows are removed from model.
        Connected to files_model.rowsRemoved signal.
        """
        self._rebuild_file_indices()
    
    def _on_data_changed(self, topLeft, bottomRight):
        """
        Auto-sync cache when data changes in model.
        Connected to files_model.dataChanged signal.
        """
        for row in range(topLeft.row(), bottomRight.row() + 1):
            filename = self.files_model.item(row, 0).text()
            if filename in self.file_data_cache:
                self.file_data_cache[filename]['uploaded_date'] = self.files_model.item(row, 1).text()
                self.file_data_cache[filename]['extension'] = self.files_model.item(row, 2).text()
    
    def _get_status_emoji(self, status):
        """
        Get emoji indicator for file status.
        
        Args:
            status (str): File status
            
        Returns:
            str: Emoji + status text
        """
        status_map = {
            'available': '🟢 Available',
            'soft_deleted': '🟡 Deleted',
            'permanently_deleted': '🔴 Permanently Deleted'
        }
        return status_map.get(status, '⚪ Unknown')
    
    def _get_approval_emoji(self, approval):
        """
        Get emoji indicator for approval status.
        
        Args:
            approval (str): Approval status
            
        Returns:
            str: Emoji + approval text
        """
        approval_map = {
            'pending': '🟡 Pending',
            'accepted': '🟢 Accepted',
            'rejected': '🔴 Rejected'
        }
        return approval_map.get(approval, '⚪ Unknown')
    
    def update_collection_file_count(self, collection_id):
        """
        Update the file count indicator on a specific collection card
        
        Args:
            collection_id (int): ID of the collection to update
        """
        if collection_id not in self.collection_cards:
            print(f"Collection ID {collection_id} not found in cache")
            return
        
        # Get collection data using ID
        collection_data = self.controller._get_collection_by_id(collection_id)
        
        if not collection_data:
            print(f"Collection ID {collection_id} not found in data")
            return
        
        collection_name = collection_data.get('name', f'ID:{collection_id}')
        
        # Find the count label in the card widget
        card = self.collection_cards[collection_id]
        count_label = card.findChild(QLabel, "file_count_label")
        
        if count_label:
            file_count = len(collection_data.get('files', []))
            count_label.setText(f"Files: {file_count}")
            print(f"Updated file count for '{collection_name}' (ID: {collection_id}): {file_count}")
        else:
            print(f"Count label not found for '{collection_name}' (ID: {collection_id})")
    
    def refresh_all_collection_counts(self):
        """
        Refresh file counts for all collection cards.
        
        Useful when we don't know which specific collection changed.
        """
        print("Refreshing all collection file counts...")
        
        # Get fresh data from controller
        collections_data = self.controller.get_collections()
        
        # Update each collection card using collection ID
        for collection_data in collections_data:
            collection_id = collection_data.get('id')
            collection_name = collection_data.get('name')
            
            if collection_id is not None and collection_id in self.collection_cards:
                card = self.collection_cards[collection_id]
                count_label = card.findChild(QLabel, "file_count_label")
                
                if count_label:
                    file_count = len(collection_data.get('files', []))
                    count_label.setText(f"Files: {file_count}")
                    print(f"  - Updated '{collection_name}' (ID: {collection_id}): {file_count} files")
        
        print("All collection counts refreshed.")
        
        
    def refresh_storage_chart(self):
        """
        refresh the storage chart with updated data from the controller
        u can call this when:
        
            after uploading files and after file deletions
            (and maybe after some operations that updates
            the storage of the vault)
        
        """
        storage_data = self.controller.get_storage_info()
        if hasattr(self, 'donut_chart'):
            self.donut_chart.update_data(
                used_percentage=storage_data['usage_percentage'],
                # used_percentage=25, # for TESTING (uncomment this to show a percentage)
                used_gb=storage_data['used_size_gb'],
                total_gb=storage_data['total_size_gb']
            )
