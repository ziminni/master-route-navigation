# StudentActivities.py
import requests
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QMessageBox, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QListWidget
)
from PyQt6.QtCore import Qt

class StudentActivities(QWidget):
    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token

        # ---- config your API base + endpoints here ----
        self.api_base = "http://127.0.0.1:8000/api/"
        self.activities_url = self.api_base + "activities/"

        self.headers = {"Authorization": f"Bearer {self.token}"}

        # Add navigation callback attribute
        self.navigate_back_to_calendar = None  # Will be set by Calendar.py

        self.setWindowTitle("Activities")
        self.resize(1200, 700)

        # Header
        hdr = QVBoxLayout()
        hdr.addWidget(QLabel(f"Welcome, {self.username}"))
        hdr.addWidget(QLabel(f"Primary role: {self.primary_role}"))
        hdr.addWidget(QLabel(f"All roles: [{', '.join(self.roles)}]"))

        # Top Controls (Filters and Buttons)
        controls = QHBoxLayout()
        
        # Filter section
        filter_label = QLabel("Filter by:")
        filter_label.setStyleSheet("font-weight: bold; color: #084924; font-size: 14px;")
        
        self.combo_activity_type = QComboBox()
        self.combo_activity_type.setMinimumWidth(150)
        self.combo_activity_type.addItems([
            "All Events",
            "Academic",
            "Organizational",
            "Deadline",
            "Holiday"
        ])
        self.combo_activity_type.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 12px;
                color: #084924;
                font-weight: bold;
            }
            QComboBox:hover {
                border-color: #FDC601;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #ccc;
                selection-background-color: #FDC601;
                selection-color: #084924;
            }
        """)
        
        controls.addWidget(filter_label)
        controls.addWidget(self.combo_activity_type)
        controls.addStretch()
        
        # Back to Calendar button (NO Add Event button for students)
        self.btn_back = QPushButton("← Back to Calendar")
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #FDC601;
                color: #084924;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #e6b400;
                border: 2px solid #084924;
            }
            QPushButton:pressed {
                background-color: #cc9f00;
            }
        """)
        controls.addWidget(self.btn_back)

        # Main content area - split between upcoming events and activities table
        content_layout = QHBoxLayout()
        
        # Left side - Upcoming Events Panel
        self.setup_upcoming_events_panel()
        content_layout.addWidget(self.upcoming_events_widget)
        
        # Right side - Activities Table
        self.setup_activities_table()
        content_layout.addWidget(self.activities_widget)

        # Main Layout
        root = QVBoxLayout(self)
        root.addLayout(hdr)
        root.addLayout(controls)
        root.addLayout(content_layout)

        # Signals
        self.btn_back.clicked.connect(self.back_to_calendar)
        self.combo_activity_type.currentTextChanged.connect(self.filter_activities)

        # Initial data
        self.activities_data = []

    def setup_upcoming_events_panel(self):
        """Setup the upcoming events panel on the left side"""
        self.upcoming_events_widget = QWidget()
        self.upcoming_events_widget.setMinimumWidth(300)
        self.upcoming_events_widget.setMaximumWidth(400)
        self.upcoming_events_widget.setStyleSheet("background-color: white;")
        
        upcoming_layout = QVBoxLayout(self.upcoming_events_widget)
        upcoming_layout.setContentsMargins(10, 10, 10, 10)
        
        # Upcoming Events Frame
        upcoming_frame = QWidget()
        upcoming_frame.setStyleSheet("""
            QWidget {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #FFFFFF;
                padding: 10px;
            }
        """)
        frame_layout = QVBoxLayout(upcoming_frame)
        
        # Title
        title_label = QLabel("Upcoming Events")
        title_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #084924; 
            padding: 10px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(title_label)
        
        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(8)
        
        legend_style = """
            QLabel {
                padding: 5px 8px;
                border-radius: 3px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                font-size: 11px;
                font-weight: 500;
            }
        """
        
        label_academic = QLabel("🟢 Academic")
        label_academic.setStyleSheet(legend_style)
        label_org = QLabel("🔵 Organizational")
        label_org.setStyleSheet(legend_style)
        label_deadline = QLabel("🟠 Deadlines")
        label_deadline.setStyleSheet(legend_style)
        label_holiday = QLabel("🔴 Holidays")
        label_holiday.setStyleSheet(legend_style)
        
        legend_layout.addWidget(label_academic)
        legend_layout.addWidget(label_org)
        legend_layout.addWidget(label_deadline)
        legend_layout.addWidget(label_holiday)
        
        frame_layout.addLayout(legend_layout)
        
        # Filter dropdown
        self.combo_upcoming_filter = QComboBox()
        self.combo_upcoming_filter.setStyleSheet("""
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px 12px;
                background-color: white;
                min-width: 150px;
                color: #666;
                font-size: 12px;
                margin: 10px 0px;
            }
            QComboBox:hover {
                border-color: #FDC601;
            }
            QComboBox::drop-down {
                border: 0px;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #ccc;
                selection-background-color: #FDC601;
                selection-color: white;
                color: #084924;
            }
        """)
        self.combo_upcoming_filter.addItems([
            "All Events",
            "Academic Activities",
            "Organizational Activities",
            "Deadlines",
            "Holidays"
        ])
        self.combo_upcoming_filter.currentTextChanged.connect(self.on_upcoming_filter_changed)
        frame_layout.addWidget(self.combo_upcoming_filter)
        
        # Upcoming events list
        self.list_upcoming = QListWidget()
        self.list_upcoming.setMinimumHeight(400)
        self.list_upcoming.setStyleSheet("""
            QListWidget {
                background-color: white;
                color: black;
                border-radius: 8px;
                padding: 8px;
                border: 1px solid #ddd;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #FDC601;
                color: white;
                border-radius: 4px;
            }
        """)
        frame_layout.addWidget(self.list_upcoming)
        
        upcoming_layout.addWidget(upcoming_frame)

    def setup_activities_table(self):
        """Setup the activities table on the right side"""
        self.activities_widget = QWidget()
        self.activities_widget.setStyleSheet("background-color: white;")
        
        table_layout = QVBoxLayout(self.activities_widget)
        table_layout.setContentsMargins(10, 10, 10, 10)
        
        # Table title
        table_title = QLabel("Daily Activities")
        table_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #084924;
            padding: 10px;
        """)
        table_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(table_title)
        
        # Activities Table - 5 columns for students (NO Action column)
        self.activities_table = QTableWidget(0, 5)
        self.activities_table.setMinimumSize(600, 400)
        
        # Set column headers (NO Action column)
        headers = ["Date & Time", "Event", "Type", "Location", "Status"]
        self.activities_table.setHorizontalHeaderLabels(headers)
        
        # Style the table
        self.activities_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid #FDC601;
                border-radius: 8px;
                gridline-color: #e0e0e0;
                font-size: 12px;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f0f0f0;
                color: #333;
            }
            QTableWidget::item:selected {
                background-color: #FDC601;
                color: #084924;
                font-weight: bold;
            }
            QTableWidget::item:hover {
                background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #084924;
                color: white;
                border: 1px solid #FDC601;
                padding: 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QHeaderView::section:hover {
                background-color: #0a5228;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #084924;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #FDC601;
            }
        """)
        
        # Set column widths (expanded to fill space without Action column)
        self.activities_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.activities_table.setColumnWidth(0, 150)  # Date & Time (expanded)
        self.activities_table.setColumnWidth(1, 250)  # Event (expanded)
        self.activities_table.setColumnWidth(2, 100)  # Type (expanded)
        self.activities_table.setColumnWidth(3, 150)  # Location (expanded)
        self.activities_table.setColumnWidth(4, 100)  # Status (expanded)
        
        # Set row height
        self.activities_table.verticalHeader().setDefaultSectionSize(60)
        
        # Additional settings
        self.activities_table.verticalHeader().setVisible(False)
        self.activities_table.setAlternatingRowColors(True)
        self.activities_table.setSortingEnabled(True)
        
        # Make table read-only for students
        self.activities_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        table_layout.addWidget(self.activities_table)

    def load_events(self, events):
        """Load events from MainCalendar"""
        self.activities_data = events
        self.populate_table(events)
        self.populate_upcoming_events(events)
    
    def populate_table(self, activities):
        """Populate the table with activity data (read-only for students)"""
        # Disable sorting while populating
        self.activities_table.setSortingEnabled(False)
        self.activities_table.setRowCount(0)
        
        for activity in activities:
            row_position = self.activities_table.rowCount()
            self.activities_table.insertRow(row_position)
            
            # Add data to columns (NO Action column for students)
            self.activities_table.setItem(row_position, 0, QTableWidgetItem(activity["date_time"]))
            self.activities_table.setItem(row_position, 1, QTableWidgetItem(activity["event"]))
            self.activities_table.setItem(row_position, 2, QTableWidgetItem(activity["type"]))
            self.activities_table.setItem(row_position, 3, QTableWidgetItem(activity["location"]))
            self.activities_table.setItem(row_position, 4, QTableWidgetItem(activity["status"]))
            
            # Center align all cells
            for col in range(5):
                item = self.activities_table.item(row_position, col)
                if item:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Re-enable sorting
        self.activities_table.setSortingEnabled(True)
    
    def populate_upcoming_events(self, activities):
        """Populate the upcoming events list with activity data"""
        self.list_upcoming.clear()
        
        # Define emoji icons for each event type
        type_icons = {
            "Academic": "🟢",
            "Organizational": "🔵",
            "Deadline": "🟠",
            "Holiday": "🔴"
        }
        
        for activity in activities:
            icon = type_icons.get(activity["type"], "⚪")
            event_text = f"{icon} {activity['event']}\n    {activity['date_time'].replace(chr(10), ' - ')}"
            self.list_upcoming.addItem(event_text)

    # -------- Event handlers --------
    def back_to_calendar(self):
        """Handle back to calendar button click"""
        if self.navigate_back_to_calendar:
            self.navigate_back_to_calendar()
        else:
            self._info("Navigation not configured")

    def filter_activities(self, filter_text):
        """Filter activities table based on selected type"""
        if hasattr(self, 'main_calendar'):
            filtered_events = self.main_calendar.filter_events(filter_text)
            # Update both the table and the upcoming events list
            self.populate_table(filtered_events)
            self.populate_upcoming_events(filtered_events)
    
    def on_upcoming_filter_changed(self, filter_text):
        """Handle filter change in upcoming events list"""
        if hasattr(self, 'main_calendar'):
            filtered_events = self.main_calendar.filter_events(filter_text)
            # Update only the upcoming events list
            self.populate_upcoming_events(filtered_events)

    # -------- UI helpers --------
    def _info(self, msg):
        QMessageBox.information(self, "Info", str(msg))

    def _error(self, msg):
        QMessageBox.critical(self, "Error", str(msg))