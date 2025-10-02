# Calendar.py LAYOUT FOR THE CALENDAR
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget,
    QPushButton, QComboBox, QLineEdit, QListWidget, QCalendarWidget
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from .DayView import DayView
from .AdminActivities import AdminActivities
from .StudentActivities import StudentActivities
from .AddEvent import AddEvent
from .EditEvent import EditEvent

class Calendar(QWidget):
    """Main calendar layout with all views"""
    
    def __init__(self, username, roles, primary_role, token):
        super().__init__()
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.current_view = "Month"
        
        # Callback for navigating to activities (will be set by MainCalendar.py)
        self.navigate_to_activities = None
        
        # Store events list widget reference
        self.month_events_list = None

        # Initialize main layout
        main_layout = QVBoxLayout(self)
        
        # Stacked widget for different views
        self.stacked_widget = QStackedWidget()
        
        # Setup calendar views
        self.setup_month_view()
        self.setup_day_view()
        
        # Setup activities widget based on role
        role_lower = primary_role.lower()
        if role_lower == "admin":
            self.activities_widget = AdminActivities(username, roles, primary_role, token)
        elif role_lower == "student":
            self.activities_widget = StudentActivities(username, roles, primary_role, token)
        else:
            self.activities_widget = self._create_default_widget(
                "Invalid Role", f"No activities available for role: {primary_role}"
            )
        
        # Create add/edit event widgets (admin only)
        if role_lower == "admin":
            self.add_event_widget = AddEvent(username, roles, primary_role, token)
            self.edit_event_widget = EditEvent(username, roles, primary_role, token)
        else:
            self.add_event_widget = None
            self.edit_event_widget = None
        
        # Add all widgets to stack
        self.stacked_widget.addWidget(self.month_view_container)    # Index 0
        self.stacked_widget.addWidget(self.day_view_container)      # Index 1
        self.stacked_widget.addWidget(self.activities_widget)       # Index 2
        if self.add_event_widget:
            self.stacked_widget.addWidget(self.add_event_widget)    # Index 3
        if self.edit_event_widget:
            self.stacked_widget.addWidget(self.edit_event_widget)   # Index 4
        
        main_layout.addWidget(self.stacked_widget)
        
        # Setup navigation and signals
        self.setup_navigation()
        self.connect_signals()
        
        # Start with month view
        self.show_month_view()

    def setup_month_view(self):
        """Setup month calendar view with header, controls, and upcoming events"""
        self.month_view_container = QWidget()
        container_layout = QVBoxLayout(self.month_view_container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(15)
        
        # Header
        self.setup_header(container_layout)
        
        # Controls (View selector, Activities button, Search)
        self.setup_controls(container_layout)
        
        # Content area with upcoming events and calendar
        content_layout = QHBoxLayout()
        
        # Upcoming events panel
        self.month_upcoming_panel = self.create_upcoming_events_panel()
        
        # Calendar widget - using QCalendarWidget instead of circular import
        self.calendar_widget = self.create_calendar_grid()
        
        content_layout.addWidget(self.month_upcoming_panel)
        content_layout.addWidget(self.calendar_widget)
        
        container_layout.addLayout(content_layout)

    def create_calendar_grid(self):
        """Create the actual calendar grid widget"""
        calendar_container = QWidget()
        calendar_layout = QVBoxLayout(calendar_container)
        calendar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Calendar widget
        self.calendar = QCalendarWidget()
        self.calendar.setNavigationBarVisible(True)
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        
        self.calendar.setStyleSheet("""
            /* Navigation bar at the top */
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #084924;
                min-height: 50px;
                padding: 5px;
            }
            
            /* Month/Year navigation buttons */
            QCalendarWidget QToolButton {
                color: white;
                background-color: #084924;
                font-size: 16px;
                font-weight: bold;
                padding: 8px;
                margin: 2px;
                border-radius: 4px;
                min-width: 40px;
                min-height: 40px;
            }
            
            QCalendarWidget QToolButton:hover {
                background-color: #FDC601;
                color: #084924;
            }
            
            QCalendarWidget QToolButton:pressed {
                background-color: #d4a000;
            }
            
            /* Month dropdown menu */
            QCalendarWidget QMenu {
                background-color: white;
                color: #084924;
                border: 1px solid #ddd;
            }
            
            QCalendarWidget QMenu::item:selected {
                background-color: #FDC601;
                color: white;
            }
            
            /* Year spinbox */
            QCalendarWidget QSpinBox {
                color: white;
                background-color: #084924;
                selection-background-color: #FDC601;
                selection-color: white;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #FDC601;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 80px;
                min-height: 35px;
            }
            
            QCalendarWidget QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                background-color: #FDC601;
                border-left: 1px solid #084924;
                width: 20px;
                border-top-right-radius: 3px;
            }
            
            QCalendarWidget QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                background-color: #FDC601;
                border-left: 1px solid #084924;
                width: 20px;
                border-bottom-right-radius: 3px;
            }
            
            QCalendarWidget QSpinBox::up-button:hover {
                background-color: #d4a000;
            }
            
            QCalendarWidget QSpinBox::down-button:hover {
                background-color: #d4a000;
            }
            
            QCalendarWidget QSpinBox::up-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 6px solid #084924;
                width: 0px;
                height: 0px;
            }
            
            QCalendarWidget QSpinBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #084924;
                width: 0px;
                height: 0px;
            }
            
            /* Calendar table */
            QCalendarWidget QTableView {
                background-color: white;
                selection-background-color: #FDC601;
                selection-color: white;
                border: 1px solid #ddd;
                font-size: 13px;
            }
            
            QCalendarWidget QAbstractItemView:enabled {
                color: #084924;
                background-color: white;
            }
            
            QCalendarWidget QAbstractItemView:disabled {
                color: #999;
            }
            
            /* Day of week header */
            QCalendarWidget QWidget {
                alternate-background-color: #f8f9fa;
            }
        """)
        calendar_layout.addWidget(self.calendar)
        
        return calendar_container

    def setup_header(self, layout):
        """Setup header section"""
        header_layout = QVBoxLayout()
        header_layout.addWidget(QLabel(f"Welcome, {self.username}"))
        header_layout.addWidget(QLabel(f"Primary role: {self.primary_role}"))
        header_layout.addWidget(QLabel(f"All roles: [{', '.join(self.roles)}]"))
        layout.addLayout(header_layout)

    def setup_controls(self, layout):
        """Setup controls section"""
        controls_layout = QHBoxLayout()
        
        # View selector
        view_label = QLabel("View:")
        view_label.setStyleSheet("font-weight: bold; color: #084924; font-size: 14px;")
        
        self.combo_view = QComboBox()
        self.combo_view.setMinimumWidth(100)
        self.combo_view.addItems(["Month", "Day"])
        self.combo_view.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 12px;
            }
            QComboBox:hover {
                border-color: #FDC601;
            }
        """)
        self.combo_view.currentTextChanged.connect(self.on_view_changed)
        
        controls_layout.addWidget(view_label)
        controls_layout.addWidget(self.combo_view)
        controls_layout.addStretch()
        
        # View Activities button
        self.btn_view_activities = QPushButton("View Activities")
        button_style = """
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #FDC601;
                color: #084924;
            }
            QPushButton:pressed {
                background-color: #d4a000;
            }
        """
        self.btn_view_activities.setStyleSheet(button_style)
        self.btn_view_activities.clicked.connect(self.show_activities)
        controls_layout.addWidget(self.btn_view_activities)
        
        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setFixedWidth(200)
        self.search_bar.setPlaceholderText("Search events...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px 12px;
                background-color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #FDC601;
            }
        """)
        controls_layout.addWidget(self.search_bar)
        
        layout.addLayout(controls_layout)

    def setup_day_view(self):
        """Setup day view"""
        self.day_view_container = DayView(self.username, self.roles, self.primary_role, self.token)
        # Set navigation callbacks
        self.day_view_container.navigate_back_to_calendar = self.show_month_view
        self.day_view_container.navigate_to_activities = self.show_activities

    def create_upcoming_events_panel(self):
        """Create upcoming events panel"""
        panel = QWidget()
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(400)
        panel.setStyleSheet("background-color: white;")
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(10, 10, 10, 10)
        
        # Frame
        frame = QWidget()
        frame.setStyleSheet("""
            QWidget {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #FFFFFF;
                padding: 10px;
            }
        """)
        frame_layout = QVBoxLayout(frame)
        
        # Title
        title = QLabel("Upcoming Events")
        title.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #084924; 
            padding: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(title)
        
        # Legend
        legend_layout = QHBoxLayout()
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
        for text in ["🟢 Academic", "🔵 Organizational", "🟠 Deadlines", "🔴 Holidays"]:
            label = QLabel(text)
            label.setStyleSheet(legend_style)
            legend_layout.addWidget(label)
        frame_layout.addLayout(legend_layout)
        
        # Filter
        self.month_filter_combo = QComboBox()
        self.month_filter_combo.setStyleSheet("""
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
        """)
        self.month_filter_combo.addItems([
            "All Events",
            "Academic Activities",
            "Organizational Activities",
            "Deadlines",
            "Holidays"
        ])
        self.month_filter_combo.currentTextChanged.connect(self.on_month_filter_changed)
        frame_layout.addWidget(self.month_filter_combo)
        
        # Events list
        self.month_events_list = QListWidget()
        self.month_events_list.setMinimumHeight(400)
        self.month_events_list.setStyleSheet("""
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
        
        frame_layout.addWidget(self.month_events_list)
        panel_layout.addWidget(frame)
        
        return panel

    def setup_navigation(self):
        """Setup navigation callbacks"""
        if hasattr(self.activities_widget, 'navigate_back_to_calendar'):
            self.activities_widget.navigate_back_to_calendar = self.show_month_view
        
        role_lower = self.primary_role.lower()
        if role_lower == "admin":
            if hasattr(self.activities_widget, 'btn_add_event'):
                try:
                    self.activities_widget.btn_add_event.clicked.disconnect()
                except:
                    pass  # No existing connection
                self.activities_widget.btn_add_event.clicked.connect(self.show_add_event)
            
            if hasattr(self.activities_widget, 'navigate_to_edit_event'):
                self.activities_widget.navigate_to_edit_event = self.show_edit_event
            
            if self.add_event_widget:
                self.add_event_widget.navigate_back_to_activities = self.show_activities
            
            if self.edit_event_widget:
                self.edit_event_widget.navigate_back_to_activities = self.show_activities

    def connect_signals(self):
        """Connect signals"""
        pass

    def on_view_changed(self, view_type):
        """Handle view change from dropdown"""
        self.current_view = view_type
        if view_type == "Month":
            self.show_month_view()
        elif view_type == "Day":
            self.show_day_view()

    def show_month_view(self):
        """Show month calendar view"""
        self.stacked_widget.setCurrentIndex(0)
        self.current_view = "Month"
        # Update combo box without triggering signal
        if hasattr(self, 'combo_view'):
            self.combo_view.blockSignals(True)
            self.combo_view.setCurrentText("Month")
            self.combo_view.blockSignals(False)

    def show_day_view(self):
        """Show day view"""
        self.stacked_widget.setCurrentIndex(1)
        self.current_view = "Day"
        # Update the month view combo box without triggering signal
        if hasattr(self, 'combo_view'):
            self.combo_view.blockSignals(True)
            self.combo_view.setCurrentText("Day")
            self.combo_view.blockSignals(False)

    def show_activities(self):
        """Show activities view"""
        if self.navigate_to_activities:
            self.navigate_to_activities()

    def show_add_event(self):
        """Show add event view"""
        if self.add_event_widget:
            self.stacked_widget.setCurrentIndex(3)

    def show_edit_event(self, event_data=None):
        """Show edit event view"""
        if self.edit_event_widget:
            if event_data:
                self.edit_event_widget.event_data = event_data
                self.edit_event_widget.load_event_data()
            self.stacked_widget.setCurrentIndex(4)
    
    def load_events(self, events):
        """Load events from MainCalendar into month view and day view"""
        # Load into month view upcoming events panel
        if self.month_events_list is not None:
            self.month_events_list.clear()
            type_icons = {
                "Academic": "🟢",
                "Organizational": "🔵",
                "Deadline": "🟠",
                "Holiday": "🔴"
            }
            for event in events:
                icon = type_icons.get(event["type"], "⚪")
                event_text = f"{icon} {event['event']}\n    {event['date_time'].replace(chr(10), ' - ')}"
                self.month_events_list.addItem(event_text)
        
        # Load into day view
        if hasattr(self, 'day_view_container') and hasattr(self.day_view_container, 'load_events'):
            self.day_view_container.load_events(events)
    
    def on_month_filter_changed(self, filter_text):
        """Handle filter change in month view upcoming events"""
        if hasattr(self, 'main_calendar'):
            filtered_events = self.main_calendar.filter_events(filter_text)
            # Update the month view upcoming events list
            if self.month_events_list is not None:
                self.month_events_list.clear()
                type_icons = {
                    "Academic": "🟢",
                    "Organizational": "🔵",
                    "Deadline": "🟠",
                    "Holiday": "🔴"
                }
                for event in filtered_events:
                    icon = type_icons.get(event["type"], "⚪")
                    event_text = f"{icon} {event['event']}\n    {event['date_time'].replace(chr(10), ' - ')}"
                    self.month_events_list.addItem(event_text)

    def _create_default_widget(self, title, desc):
        """Create fallback widget"""
        widget = QWidget()
        layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        desc_label = QLabel(desc)
        desc_label.setFont(QFont("Arial", 12))
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        widget.setLayout(layout)
        return widget