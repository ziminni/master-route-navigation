from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QLineEdit
from .appointment_crud import appointment_crud

class StudentBrowseFaculty_ui(QWidget):
    go_to_RequestPage = QtCore.pyqtSignal(dict)  # Emit faculty data
    back = QtCore.pyqtSignal()

    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.Appointment_crud = appointment_crud()
        
        self.setWindowTitle("Appointment Scheduler")
        self.current_page = 0
        self.items_per_page = 6
        self.faculties = []
        self.filtered_faculties = []
        self.setFixedSize(1000, 550)
        self._setupBrowseFacultyPage()
        self.load_faculties_data()
       
    def load_faculties_data(self):
        """Load faculty data from JSON database"""
        try:
            faculties_data = self.Appointment_crud.list_faculty()
            self.faculties = []
            
            for faculty in faculties_data:
                self.faculties.append({
                    "id": faculty.get('id'),
                    "name": faculty.get('name', 'Unknown'),
                    "email": faculty.get('email', 'No email'),
                    "department": faculty.get('department', 'Unknown Department'),
                    "role": "Request"
                })
            
            if not self.faculties:
                self._create_sample_faculties()
                faculties_data = self.Appointment_crud.list_faculty()
                for faculty in faculties_data:
                    self.faculties.append({
                        "id": faculty.get('id'),
                        "name": faculty.get('name', 'Unknown'),
                        "email": faculty.get('email', 'No email'),
                        "department": faculty.get('department', 'Unknown Department'),
                        "role": "Request"
                    })
            
            # Initialize filtered faculties with all faculties
            self.filtered_faculties = self.faculties.copy()
            self._populateFacultiesGrid()
            
        except Exception as e:
            print(f"Error loading faculties data: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load faculty data: {str(e)}")
            self.faculties = [
                {"id": 1, "name": "Dr. Smith", "email": "smith@university.edu", "department": "Computer Science", "role": "Request"},
                {"id": 2, "name": "Prof. Johnson", "email": "johnson@university.edu", "department": "Mathematics", "role": "Request"},
                {"id": 3, "name": "Dr. Brown", "email": "brown@university.edu", "department": "Physics", "role": "Request"},
                {"id": 4, "name": "Prof. Davis", "email": "davis@university.edu", "department": "Chemistry", "role": "Request"},
                {"id": 5, "name": "Dr. Wilson", "email": "wilson@university.edu", "department": "Biology", "role": "Request"},
                {"id": 6, "name": "Prof. Taylor", "email": "taylor@university.edu", "department": "Engineering", "role": "Request"},
            ]
            self.filtered_faculties = self.faculties.copy()
            self._populateFacultiesGrid()

    def _create_sample_faculties(self):
        """Create sample faculty data if none exists"""
        try:
            sample_faculties = [
                {"name": "Dr. Smith", "email": "smith@university.edu", "department": "Computer Science"},
                {"name": "Prof. Johnson", "email": "johnson@university.edu", "department": "Mathematics"},
                {"name": "Dr. Brown", "email": "brown@university.edu", "department": "Physics"},
                {"name": "Prof. Davis", "email": "davis@university.edu", "department": "Chemistry"},
                {"name": "Dr. Wilson", "email": "wilson@university.edu", "department": "Biology"},
                {"name": "Prof. Taylor", "email": "taylor@university.edu", "department": "Engineering"},
                {"name": "Dr. Anderson", "email": "anderson@university.edu", "department": "Psychology"},
                {"name": "Prof. Martinez", "email": "martinez@university.edu", "department": "Sociology"},
                {"name": "Dr. Clark", "email": "clark@university.edu", "department": "Economics"},
                {"name": "Prof. Rodriguez", "email": "rodriguez@university.edu", "department": "Business"},
            ]
            
            for faculty in sample_faculties:
                self.Appointment_crud.create_faculty(
                    faculty["name"],
                    faculty["email"],
                    faculty["department"]
                )
                
        except Exception as e:
            print(f"Error creating sample faculties: {e}")

    def _setupBrowseFacultyPage(self):
        self.setObjectName("AppointmentScheduler")
        
        scheduler_layout = QtWidgets.QVBoxLayout(self)
        scheduler_layout.setContentsMargins(0, 0, 0, 0)
        scheduler_layout.setSpacing(10)
        
        header_widget = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.Academics_5 = QtWidgets.QLabel()
        font = QtGui.QFont()
        font.setFamily("Poppins")
        font.setPointSize(24)
        self.Academics_5.setFont(font)
        self.Academics_5.setStyleSheet("QLabel { color: #084924; }")
        self.Academics_5.setObjectName("Academics_5")
        
        header_layout.addWidget(self.Academics_5)
        header_layout.addStretch(1)

        self.refreshButton = QtWidgets.QPushButton("Refresh")
        self.refreshButton.setFixedSize(100, 35)
        self.refreshButton.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border-radius: 8px;
                margin-right: 10px;
                font: 10pt 'Poppins';
            }
            QPushButton:hover {
                background-color: #2a75e0;
            }
        """)
        self.refreshButton.clicked.connect(self.load_faculties_data)
        header_layout.addWidget(self.refreshButton)

        self.backbutton = QtWidgets.QPushButton("<- Back")
        self.backbutton.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #084924, stop:1 #0a5a2f);
                color: white;
                border: none;
                border-radius: 8px;
                font: 600 11pt 'Poppins';
                padding: 8px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0a5a2f, stop:1 #0c6b3a);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06381b, stop:1 #084924);
            }
        """)
        self.backbutton.setFixedSize(100, 40)
        self.backbutton.clicked.connect(self.back)
        header_layout.addWidget(self.backbutton)
        
        scheduler_layout.addWidget(header_widget)
        
        self.widget_25 = QtWidgets.QWidget()
        self.widget_25.setStyleSheet("QWidget#widget_25 { background-color: #FFFFFF; border-radius: 20px; }")
        self.widget_25.setObjectName("widget_25")
        
        widget_layout = QtWidgets.QVBoxLayout(self.widget_25)
        widget_layout.setContentsMargins(20, 20, 20, 20)
        widget_layout.setSpacing(15)
        
        self._setupFacultiesSection(widget_layout)
        
        scheduler_layout.addWidget(self.widget_25, 1)
        
        self.retranslateUi()

    def _setupFacultiesSection(self, parent_layout):
        faculties_container = QtWidgets.QWidget()
        faculties_container.setObjectName("faculties_container")
        
        faculties_layout = QtWidgets.QVBoxLayout(faculties_container)
        faculties_layout.setContentsMargins(0, 0, 0, 0)
        faculties_layout.setSpacing(15)
        
        # Search bar section
        self._setupSearchBar(faculties_layout)
        
        faculties_header = QtWidgets.QLabel()
        faculties_header.setObjectName("faculties_header")
        faculties_header.setStyleSheet("""
            QLabel {
                font: 14pt 'Poppins';
                color: #000000;
                padding: 8px 0;
            }
        """)
        faculties_layout.addWidget(faculties_header)
        
        self.faculties_scroll_area = QtWidgets.QScrollArea()
        self.faculties_scroll_area.setWidgetResizable(True)
        self.faculties_scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.faculties_scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.faculties_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
        """)
        
        self.faculties_grid_widget = QtWidgets.QWidget()
        self.faculties_grid_layout = QtWidgets.QGridLayout(self.faculties_grid_widget)
        self.faculties_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.faculties_grid_layout.setHorizontalSpacing(20)
        self.faculties_grid_layout.setVerticalSpacing(15)
        
        self.faculties_scroll_area.setWidget(self.faculties_grid_widget)
        faculties_layout.addWidget(self.faculties_scroll_area, 1)
        
        self._setupPaginationControls(faculties_layout)
        
        parent_layout.addWidget(faculties_container, 1)

    def _setupSearchBar(self, parent_layout):
        """Setup search bar with filter options"""
        search_container = QtWidgets.QWidget()
        search_layout = QtWidgets.QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search faculty by name, email, or department...")
        self.search_input.setFixedHeight(40)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #084924;
                border-radius: 8px;
                padding: 8px 12px;
                font: 11pt 'Poppins';
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #0a5a2f;
                background-color: #f8fff8;
            }
            QLineEdit::placeholder {
                color: #999999;
                font: 10pt 'Poppins';
            }
        """)
        self.search_input.textChanged.connect(self._onSearchTextChanged)
        
        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.setFixedSize(100, 40)
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border-radius: 8px;
                font: 600 11pt 'Poppins';
                border: none;
            }
            QPushButton:hover {
                background-color: #0a5a2f;
            }
            QPushButton:pressed {
                background-color: #063818;
            }
        """)
        self.search_button.clicked.connect(self._performSearch)
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setFixedSize(80, 40)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border-radius: 8px;
                font: 600 11pt 'Poppins';
                border: none;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.clear_button.clicked.connect(self._clearSearch)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.clear_button)
        
        parent_layout.addWidget(search_container)

    def _setupPaginationControls(self, parent_layout):
        pagination_widget = QtWidgets.QWidget()
        pagination_layout = QtWidgets.QHBoxLayout(pagination_widget)
        pagination_layout.setContentsMargins(0, 10, 0, 0)
        
        self.prev_button = QtWidgets.QPushButton("Previous")
        self.prev_button.setFixedSize(100, 35)
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border-radius: 8px;
                font: 10pt 'Poppins';
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.prev_button.clicked.connect(self._previousPage)
        
        self.page_info = QtWidgets.QLabel()
        self.page_info.setStyleSheet("""
            QLabel {
                font: 10pt 'Poppins';
                color: #000000;
            }
        """)
        self.page_info.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        self.next_button = QtWidgets.QPushButton("Next")
        self.next_button.setFixedSize(100, 35)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border-radius: 8px;
                font: 10pt 'Poppins';
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.next_button.clicked.connect(self._nextPage)
        
        pagination_layout.addStretch(1)
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addSpacing(10)
        pagination_layout.addWidget(self.page_info)
        pagination_layout.addSpacing(10)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addStretch(1)
        
        parent_layout.addWidget(pagination_widget)

    def _onSearchTextChanged(self, text):
        """Handle real-time search as user types"""
        if text.strip():
            self._performSearch()
        else:
            self._clearSearch()

    def _performSearch(self):
        """Perform search based on current search text"""
        search_text = self.search_input.text().strip().lower()
        
        if not search_text:
            self.filtered_faculties = self.faculties.copy()
        else:
            self.filtered_faculties = [
                faculty for faculty in self.faculties
                if (search_text in faculty["name"].lower() or
                    search_text in faculty["email"].lower() or
                    search_text in faculty["department"].lower())
            ]
        
        # Reset to first page after search
        self.current_page = 0
        self._populateFacultiesGrid()
        
        # Update results count
        self._updateSearchResultsCount()

    def _clearSearch(self):
        """Clear search and show all faculties"""
        self.search_input.clear()
        self.filtered_faculties = self.faculties.copy()
        self.current_page = 0
        self._populateFacultiesGrid()
        self._updateSearchResultsCount()

    def _updateSearchResultsCount(self):
        """Update the header to show search results count"""
        faculties_header = self.findChild(QtWidgets.QLabel, "faculties_header")
        if faculties_header:
            if self.search_input.text().strip():
                total_count = len(self.faculties)
                filtered_count = len(self.filtered_faculties)
                faculties_header.setText(f"Found {filtered_count} of {total_count} faculties")
            else:
                faculties_header.setText(f"See Available Faculties ({len(self.faculties)} total)")

    def _populateFacultiesGrid(self):
        """Populate the grid with filtered faculties"""
        # Clear existing items
        for i in reversed(range(self.faculties_grid_layout.count())):
            widget = self.faculties_grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Calculate start and end indices for current page
        start_index = self.current_page * self.items_per_page
        end_index = min(start_index + self.items_per_page, len(self.filtered_faculties))
        
        # Show message if no results
        if not self.filtered_faculties:
            no_results_label = QtWidgets.QLabel("No faculties found matching your search criteria.")
            no_results_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            no_results_label.setStyleSheet("""
                QLabel {
                    font: 12pt 'Poppins';
                    color: #666666;
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 40px;
                    margin: 20px;
                }
            """)
            self.faculties_grid_layout.addWidget(no_results_label, 0, 0, 1, 3)
            return
        
        # Add faculty cards for current page
        for i in range(start_index, end_index):
            faculty = self.filtered_faculties[i]
            position = i - start_index
            row = position // 3
            col = position % 3
            
            faculty_card = self._createFacultyCard(faculty)
            self.faculties_grid_layout.addWidget(faculty_card, row, col)
        
        # Update pagination info
        total_pages = (len(self.filtered_faculties) + self.items_per_page - 1) // self.items_per_page
        self.page_info.setText(f"Page {self.current_page + 1} of {total_pages}")
        
        # Update button states
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

    def _createFacultyCard(self, faculty):
        card = QtWidgets.QWidget()
        card.setFixedSize(250, 300)
        card.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border: 2px solid #E0E0E0;
                border-radius: 15px;
            }
            QWidget:hover {
                border: 2px solid #084924;
                background-color: #F8FFF8;
            }
        """)
        
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(10)
        
        # Profile image placeholder
        profile_image = QLabel()
        profile_image.setFixedSize(80, 80)
        profile_image.setStyleSheet("""
            QLabel {
                background-color: #0078D4;
                border-radius: 40px;
            }
        """)
        card_layout.addWidget(profile_image, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        
        # Email label
        email_label = QLabel(faculty["email"])
        email_label.setStyleSheet("""
            QLabel {
                font: 12pt 'Poppins';
                color: #064420;
                text-align: center;
            }
        """)
        email_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        email_label.setWordWrap(True)
        card_layout.addWidget(email_label)
        
        # Name label
        name_label = QLabel(faculty["name"])
        name_label.setStyleSheet("""
            QLabel {
                font: 14pt 'Poppins';
                color: #000000;
                text-align: center;
            }
        """)
        name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(name_label)
        
        # Department label
        dept_label = QLabel(faculty["department"])
        dept_label.setStyleSheet("""
            QLabel {
                font: 11pt 'Poppins';
                color: #666666;
                text-align: center;
            }
        """)
        dept_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(dept_label)
        
        # Request button
        request_button = QPushButton(faculty["role"])
        request_button.setFixedSize(230, 40)
        active_block = self.Appointment_crud.get_active_block(faculty["id"])
        if active_block and "error" not in active_block:
            request_button.setEnabled(True)
            request_button.setStyleSheet("""
                QPushButton {
                    background-color: #084924;
                    color: white;
                    border-radius: 8px;
                    font: bold 12pt 'Poppins';
                    border: none;
                }
                QPushButton:hover {
                    background-color: #0a5a2f;
                }
                QPushButton:pressed {
                    background-color: #063818;
                }
            """)
        else:
            request_button.setEnabled(False)
            request_button.setToolTip("No available schedule")
            request_button.setText("No available schedule")
            request_button.setStyleSheet("""
                QPushButton {
                    background-color: #E0E0E0;
                    color: black;
                    border-radius: 8px;
                }
            """)
        
        request_button.clicked.connect(lambda checked, f=faculty: self._onRequestClicked(f))
        
        button_container = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch(1)
        button_layout.addWidget(request_button)
        button_layout.addStretch(1)
        
        card_layout.addWidget(button_container)
        
        return card

    def _onRequestClicked(self, faculty):
        """Handle request button click"""
        print(f"Request appointment with {faculty['name']}")
        try:
            active_block = self.Appointment_crud.get_active_block(faculty["id"])
            if active_block and "error" not in active_block:
                self.go_to_RequestPage.emit(faculty)
            else:
                QMessageBox.information(
                    self,
                    "No Available Schedule",
                    f"{faculty['name']} doesn't have any available schedule at the moment.\n\nPlease check back later or contact the faculty directly."
                )
        except Exception as e:
            print(f"Error checking faculty availability: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to check faculty availability: {str(e)}"
            )

    def _previousPage(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._populateFacultiesGrid()

    def _nextPage(self):
        total_pages = (len(self.filtered_faculties) + self.items_per_page - 1) // self.items_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._populateFacultiesGrid()

    def retranslateUi(self):
        self.Academics_5.setText("Faculties")
        self._updateSearchResultsCount()  # Initialize the header text