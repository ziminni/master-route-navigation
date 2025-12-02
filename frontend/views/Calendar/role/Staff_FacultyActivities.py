import requests
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QMessageBox, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QListWidget, QGridLayout
)


class StaffFacultyActivities(QWidget):
    def __init__(self, username, roles, primary_role, token, parent=None):
        super().__init__(parent)
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token

        # API config
        self.api_base = "http://127.0.0.1:8000/api/"
        self.activities_url = self.api_base + "activities/"
        self.headers = {"Authorization": f"Bearer {self.token}"}

        # Navigation callbacks (set from MainCalendar/Calendar)
        self.navigate_back_to_calendar = None
        self.navigate_to_add_event = None
        self.main_calendar = None

        # Toggle state for upcoming events panel
        self.upcoming_events_visible = True

        self.setWindowTitle("Activities")
        self.resize(1200, 700)

        # ---------- Top controls ----------
        controls = QHBoxLayout()

        # Toggle Upcoming Events button
        self.btn_toggle_upcoming = QPushButton("◀ Hide Panel")
        self.btn_toggle_upcoming.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                padding: 10px 15px;
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
        """)
        self.btn_toggle_upcoming.clicked.connect(self.toggle_upcoming_events)
        controls.addWidget(self.btn_toggle_upcoming)

        controls.addSpacing(20)

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

        # Add Event button
        button_style = """
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #FDC601;
                color: #084924;
            }
            QPushButton:pressed {
                background-color: #d4a000;
            }
        """
        self.btn_add_event = QPushButton("+ Add Event")
        self.btn_add_event.setStyleSheet(button_style)
        controls.addWidget(self.btn_add_event)

        # Back to Calendar button
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

        # ---------- Main content area ----------
        self.content_layout = QHBoxLayout()

        # Left side - Upcoming Events Panel
        self.setup_upcoming_events_panel()
        self.content_layout.addWidget(self.upcoming_events_widget)

        # Right side - Activities Table
        self.setup_activities_table()
        self.content_layout.addWidget(self.activities_widget)

        # Let table side expand more
        self.content_layout.setStretch(0, 0)
        self.content_layout.setStretch(1, 1)

        # ---------- Root layout ----------
        root = QVBoxLayout(self)
        root.addLayout(controls)
        root.addLayout(self.content_layout)

        # Signals
        self.btn_back.clicked.connect(self.back_to_calendar)
        self.btn_add_event.clicked.connect(self.add_event)
        self.combo_activity_type.currentTextChanged.connect(self.filter_activities)

        # Data
        self.activities_data = []

    # ---------- Toggle panel ----------

    def toggle_upcoming_events(self):
        """Toggle visibility of upcoming events panel."""
        if self.upcoming_events_visible:
            self.upcoming_events_widget.setVisible(False)
            self.content_layout.setStretch(0, 0)
            self.content_layout.setStretch(1, 1)
            self.btn_toggle_upcoming.setText("▶ Show Panel")
        else:
            self.upcoming_events_widget.setVisible(True)
            self.content_layout.setStretch(0, 0)
            self.content_layout.setStretch(1, 1)
            self.btn_toggle_upcoming.setText("◀ Hide Panel")
        self.upcoming_events_visible = not self.upcoming_events_visible

    # ---------- Upcoming events panel ----------

    def setup_upcoming_events_panel(self):
        self.upcoming_events_widget = QWidget()
        self.upcoming_events_widget.setMinimumWidth(300)
        self.upcoming_events_widget.setMaximumWidth(400)
        self.upcoming_events_widget.setStyleSheet("background-color: white;")

        upcoming_layout = QVBoxLayout(self.upcoming_events_widget)
        upcoming_layout.setContentsMargins(10, 10, 10, 10)

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

        title_label = QLabel("Upcoming Events")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #084924;
            padding: 10px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(title_label)

        legend_grid = QGridLayout()
        legend_grid.setSpacing(8)
        legend_grid.setContentsMargins(5, 5, 5, 5)

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

        legend_grid.addWidget(label_academic, 0, 0)
        legend_grid.addWidget(label_org, 0, 1)
        legend_grid.addWidget(label_deadline, 1, 0)
        legend_grid.addWidget(label_holiday, 1, 1)

        frame_layout.addLayout(legend_grid)

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

    # ---------- Activities table ----------

    def setup_activities_table(self):
        """Setup the activities table on the right side (read‑only for staff/faculty)."""
        self.activities_widget = QWidget()
        self.activities_widget.setStyleSheet("background-color: white;")

        container_layout = QVBoxLayout(self.activities_widget)
        container_layout.setContentsMargins(10, 10, 10, 10)

        h_layout = QHBoxLayout()
        h_layout.addStretch()

        table_wrapper = QWidget()
        table_layout = QVBoxLayout(table_wrapper)

        table_title = QLabel("Daily Activities")
        table_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #084924;
            padding: 10px;
        """)
        table_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(table_title)

        self.activities_table = QTableWidget(0, 5)
        self.activities_table.setMinimumSize(750, 400)

        headers = ["Date & Time", "Event", "Type", "Location", "Status"]
        self.activities_table.setHorizontalHeaderLabels(headers)

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

        self.activities_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.activities_table.setColumnWidth(0, 120)
        self.activities_table.setColumnWidth(1, 250)
        self.activities_table.setColumnWidth(2, 125)
        self.activities_table.setColumnWidth(3, 150)
        self.activities_table.setColumnWidth(4, 100)

        self.activities_table.verticalHeader().setDefaultSectionSize(60)
        self.activities_table.verticalHeader().setVisible(False)
        self.activities_table.setAlternatingRowColors(True)
        self.activities_table.setSortingEnabled(False)
        self.activities_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        table_layout.addWidget(self.activities_table)

        h_layout.addWidget(table_wrapper)
        h_layout.addStretch()

        container_layout.addLayout(h_layout)

    # ---------- Data loading ----------

    def load_events(self, events):
        self.activities_data = events
        self.populate_table(events)
        self.populate_upcoming_events(events)

    def populate_table(self, activities):
        self.activities_table.setSortingEnabled(False)
        self.activities_table.setRowCount(0)

        sorted_activities = self._sort_activities_by_priority(activities)

        for activity in sorted_activities:
            row = self.activities_table.rowCount()
            self.activities_table.insertRow(row)

            self.activities_table.setItem(row, 0, QTableWidgetItem(activity["date_time"]))
            self.activities_table.setItem(row, 1, QTableWidgetItem(activity["event"]))
            self.activities_table.setItem(row, 2, QTableWidgetItem(activity["type"]))
            self.activities_table.setItem(row, 3, QTableWidgetItem(activity["location"]))
            self.activities_table.setItem(row, 4, QTableWidgetItem(activity["status"]))

            for col in range(5):
                item = self.activities_table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.activities_table.setSortingEnabled(False)

    def populate_upcoming_events(self, activities):
        self.list_upcoming.clear()

        type_icons = {
            "Academic": "🟢",
            "Organizational": "🔵",
            "Deadline": "🟠",
            "Holiday": "🔴"
        }

        upcoming_events = self._filter_upcoming_events(activities)

        for activity in upcoming_events:
            icon = type_icons.get(activity.get("type"), "⚪")
            text = activity.get("date_time", "").replace(chr(10), " - ")
            item_text = f"{icon} {activity.get('event', '')}\n    {text}"
            self.list_upcoming.addItem(item_text)

    # ---------- Sorting and filtering helpers ----------

    def _sort_activities_by_priority(self, events):
        today = datetime.now().date()
        current_month = today.month
        current_year = today.year

        current_month_upcoming = []
        future_months = []
        current_month_past = []
        old_past_events = []

        for event in events:
            date_str = event.get('date_time', '')
            try:
                if '\n' in date_str:
                    date_part = date_str.split('\n')[0].strip()
                else:
                    date_part = date_str.strip()
                event_date = datetime.strptime(date_part, "%m/%d/%Y").date()

                if event_date < today:
                    event['status'] = "Finished"
                elif event.get('status') == "Finished":
                    event['status'] = "Upcoming"

                if event_date.month == current_month and event_date.year == current_year:
                    if event_date >= today:
                        current_month_upcoming.append((event_date, event))
                    else:
                        current_month_past.append((event_date, event))
                elif event_date > today:
                    future_months.append((event_date, event))
                else:
                    old_past_events.append((event_date, event))

            except (ValueError, IndexError):
                print(f"Warning: Could not parse date for event '{event.get('event', 'Unknown')}': {date_str}")
                old_past_events.append((datetime.max.date(), event))
                continue

        current_month_upcoming.sort(key=lambda x: x[0])
        current_month_past.sort(key=lambda x: x[0])
        future_months.sort(key=lambda x: x[0])
        old_past_events.sort(key=lambda x: x[0])

        return (
            [e for _, e in current_month_upcoming] +
            [e for _, e in future_months] +
            [e for _, e in current_month_past] +
            [e for _, e in old_past_events]
        )

    def _filter_upcoming_events(self, events):
        today = datetime.now().date()
        upcoming = []

        for event in events:
            date_str = event.get('date_time', '')
            try:
                if '\n' in date_str:
                    date_part = date_str.split('\n')[0].strip()
                else:
                    date_part = date_str.strip()
                event_date = datetime.strptime(date_part, "%m/%d/%Y").date()
                if event_date >= today:
                    upcoming.append(event)
            except (ValueError, IndexError):
                print(f"Warning: Could not parse date for event '{event.get('event', 'Unknown')}': {date_str}")
                continue

        def get_event_date(ev):
            ds = ev.get('date_time', '')
            try:
                if '\n' in ds:
                    dp = ds.split('\n')[0].strip()
                else:
                    dp = ds.strip()
                return datetime.strptime(dp, "%m/%d/%Y").date()
            except Exception:
                return datetime.max.date()

        upcoming.sort(key=get_event_date)
        return upcoming

    # ---------- Event handlers ----------

    def back_to_calendar(self):
        if self.navigate_back_to_calendar:
            self.navigate_back_to_calendar()
        else:
            self._info("Navigation not configured")

    def add_event(self):
        if self.navigate_to_add_event:
            self.navigate_to_add_event()
        else:
            self._info("Add Event navigation not configured")

    def filter_activities(self, filter_text):
        if hasattr(self, 'main_calendar') and self.main_calendar:
            filtered = self.main_calendar.filter_events(filter_text)
            self.populate_table(filtered)
            self.populate_upcoming_events(filtered)

    def on_upcoming_filter_changed(self, filter_text):
        if hasattr(self, 'main_calendar') and self.main_calendar:
            filtered = self.main_calendar.filter_events(filter_text)
            self.populate_upcoming_events(filtered)

    # ---------- Helpers ----------

    def _info(self, msg):
        QMessageBox.information(self, "Info", str(msg))

    def _error(self, msg):
        QMessageBox.critical(self, "Error", str(msg))
