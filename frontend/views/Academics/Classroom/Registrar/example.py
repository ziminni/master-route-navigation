import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTableView,
                             QStackedWidget, QComboBox, QHeaderView)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QFont, QIcon, QColor


# Table Models
class SectionsTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self._headers = ['No.', 'Section', 'Program', 'Year', 'Type', 'Capacity', 'Remarks']
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = self._data[index.row()]
        col = index.column()
        value = list(row.values())[col]
        
        if role == Qt.ItemDataRole.DisplayRole:
            return str(value)
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            # Center-align numeric columns (No., Year, Capacity)
            if col in [0, 3, 5]:
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        elif role == Qt.ItemDataRole.BackgroundRole:
            # Handle background for selected and alternate rows
            if index.row() % 2 == 0:
                return QColor("#ffffff")
            return QColor("#f5f5f5")
        elif role == Qt.ItemDataRole.ForegroundRole:
            # Ensure text is visible when selected
            return QColor("#2d2d2d")
        return None
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        elif role == Qt.ItemDataRole.TextAlignmentRole and orientation == Qt.Orientation.Horizontal:
            return Qt.AlignmentFlag.AlignCenter
        return None
    
    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        # Items stay visible and "enabled" but cannot be selected or edited
        return Qt.ItemFlag.ItemIsEnabled



class ClassesTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self._headers = ['No.', 'Code', 'Title', 'Units', 'Section', 'Schedule', 
                        'Room', 'Instructor', 'Type', '']
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = self._data[index.row()]
        col = index.column()
        
        if col == 9:  # Last column for Edit button
            if role == Qt.ItemDataRole.DisplayRole:
                return None
            return None
        
        value = list(row.values())[col]
        
        if role == Qt.ItemDataRole.DisplayRole:
            return str(value)
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            # Center-align numeric columns (No., Units)
            if col in [0, 3]:
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        elif role == Qt.ItemDataRole.BackgroundRole:
            # Handle background for selected and alternate rows
            if index.row() % 2 == 0:
                return QColor("#ffffff")
            return QColor("#f5f5f5")
        elif role == Qt.ItemDataRole.ForegroundRole:
            # Ensure text is visible when selected
            return QColor("#2d2d2d")
        return None
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        elif role == Qt.ItemDataRole.TextAlignmentRole and orientation == Qt.Orientation.Horizontal:
            return Qt.AlignmentFlag.AlignCenter
        return None
    
    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        # Items stay visible and "enabled" but cannot be selected or edited
        return Qt.ItemFlag.ItemIsEnabled


# Page Widgets
class SectionsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header with title and add button
        header_layout = QHBoxLayout()
        title = QLabel("Sections")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))
        title.setStyleSheet("color: #2d2d2d;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("⊕ Add Section")
        add_btn.setFixedHeight(40)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e5631;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d5a3d;
            }
        """)
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)
        
        # Table
        table = QTableView()
        table.setObjectName("sectionsTable")
        
        # Sample data
        data = [
            {'no': 1, 'section': 'A', 'program': 'BS Computer Science', 
             'year': 1, 'type': 'Lecture', 'capacity': 40, 'remarks': 'Regular'},
            {'no': 2, 'section': 'B', 'program': 'BS Information Technology', 
             'year': 2, 'type': 'Lecture', 'capacity': 50, 'remarks': 'Regular'}
        ]
        
        model = SectionsTableModel(data)
        table.setModel(model)
        
        # Table styling
        table.setStyleSheet("""
            QTableView {
                background-color: white;
                border-radius: 8px;
                gridline-color: #e0e0e0;
                selection-background-color: #1e5631;
                selection-color: white;
            }
            QTableView::item {
                padding: 10px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableView::item:alternate {
                background-color: #f5f5f5;
            }
            QHeaderView::section {
                background-color: #1e5631;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setMinimumSectionSize(100)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        # table.setSelectionBehavior(QTableView.SelectionBehavior.)
        # table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        
        # Set reasonable column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(0, 60)  # No.
        table.setColumnWidth(1, 80)  # Section
        table.setColumnWidth(2, 200) # Program
        table.setColumnWidth(3, 60)  # Year
        table.setColumnWidth(4, 100) # Type
        table.setColumnWidth(5, 80)  # Capacity
        
        layout.addWidget(table)
        self.setLayout(layout)


class ClassesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        title = QLabel("Classes")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))
        title.setStyleSheet("color: #2d2d2d;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Sort by dropdown
        sort_combo = QComboBox()
        sort_combo.addItems(["Sort by", "Code", "Title", "Section"])
        sort_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e5631;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
                min-width: 100px;
            }
            QComboBox:hover {
                background-color: #2d5a3d;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        header_layout.addWidget(sort_combo)
        
        # Add Class button
        add_btn = QPushButton("Add Class")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #2d2d2d;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover {
                background-color: #ffcd38;
            }
        """)
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)
        
        # Table
        table = QTableView()
        table.setObjectName("classesTable")
        
        # Sample data
        data = [
            {'no': 1, 'code': 'IT57', 'title': 'Fundamentals of Database', 
             'units': 3, 'section': '3A', 'schedule': 'TTH 7:00 - 7:30 AM',
             'room': 'CISC Room 3', 'instructor': 'Juan Dela Cruz', 'type': 'Regular'},
            {'no': 2, 'code': 'CS101', 'title': 'Introduction to Programming', 
             'units': 3, 'section': '1A', 'schedule': 'MW 9:00 - 10:30 AM',
             'room': 'CISC Room 1', 'instructor': 'Maria Santos', 'type': 'Regular'}
        ]
        
        model = ClassesTableModel(data)
        table.setModel(model)
        
        # Table styling
        table.setStyleSheet("""
            QTableView {
                background-color: white;
                border-radius: 8px;
                gridline-color: #e0e0e0;
                selection-background-color: #1e5631;
                selection-color: white;
            }
            QTableView::item {
                padding: 10px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableView::item:alternate {
                background-color: #f5f5f5;
            }
            QHeaderView::section {
                background-color: #1e5631;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setMinimumSectionSize(100)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        # table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableView.SelectionMode.NoSelection)

        
        # Set reasonable column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(0, 60)  # No.
        table.setColumnWidth(1, 80)  # Code
        table.setColumnWidth(2, 200) # Title
        table.setColumnWidth(3, 60)  # Units
        table.setColumnWidth(4, 80)  # Section
        table.setColumnWidth(5, 120) # Schedule
        table.setColumnWidth(6, 100) # Room
        table.setColumnWidth(7, 150) # Instructor
        table.setColumnWidth(8, 100) # Type
        table.setColumnWidth(9, 80)  # Edit button
        
        # Add Edit buttons to last column
        for row in range(model.rowCount()):
            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffc107;
                    color: #2d2d2d;
                    padding: 4px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #ffcd38;
                }
            """)
            table.setIndexWidget(model.index(row, 9), edit_btn)
        
        layout.addWidget(table)
        self.setLayout(layout)


# Main Window (unchanged, included for completeness)
class ClassroomTaggingSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Classroom Tagging System")
        self.setGeometry(100, 100, 1200, 700)
        self.init_ui()
    
    def init_ui(self):
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(130)
        # sidebar.setStyleSheet("background-color: #2d2d2d;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Hamburger menu
        menu_btn = QPushButton("☰")
        menu_btn.setFixedHeight(60)
        menu_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                font-size: 24px;
                border: none;
                border-bottom: 1px solid #3d3d3d;
            }
        """)
        sidebar_layout.addWidget(menu_btn)
        
        # Navigation buttons
        self.nav_buttons = []
        
        sections_btn = self.create_nav_button("🏠  Sections", "sections")
        classes_btn = self.create_nav_button("🏠  Classes", "classes")
        archive_btn = self.create_nav_button("📚  Archive", "archive")
        
        sidebar_layout.addWidget(sections_btn)
        sidebar_layout.addWidget(classes_btn)
        sidebar_layout.addWidget(archive_btn)
        sidebar_layout.addStretch()
        
        self.nav_buttons = [sections_btn, classes_btn, archive_btn]
        
        main_layout.addWidget(sidebar)
        
        # Content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Top header
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: white; border-bottom: 1px solid #d0d0d0;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        # header_menu = QLabel("☰")
        # header_menu.setStyleSheet("color: #666666; font-size: 20px;")
        # header_layout.addWidget(header_menu)
        
        header_title = QLabel("CLASSROOM TAGGING")
        header_title.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        header_title.setStyleSheet("color: #1e5631; margin-left: 15px;")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        
        content_layout.addWidget(header)
        
        # Stacked widget for pages
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: #f0f0f0;")
        
        # Add pages
        self.sections_page = SectionsPage()
        self.classes_page = ClassesPage()
        archive_page = QLabel("Archive")
        archive_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        archive_page.setFont(QFont("Segoe UI", 16))
        
        self.stacked_widget.addWidget(self.sections_page)
        self.stacked_widget.addWidget(self.classes_page)
        self.stacked_widget.addWidget(archive_page)
        
        content_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(content_widget)
        
        # Set initial active button
        self.set_active_nav_button(sections_btn)
    
    def create_nav_button(self, text, page_id):
        btn = QPushButton(text)
        btn.setFixedHeight(50)
        btn.setProperty("page_id", page_id)
        btn.setStyleSheet("""
            QPushButton {
                color: white;
                text-align: left;
                padding-left: 20px;
                border: none;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)
        btn.clicked.connect(lambda: self.switch_page(btn))
        return btn
    
    def switch_page(self, button):
        page_id = button.property("page_id")
        if page_id == "sections":
            self.stacked_widget.setCurrentIndex(0)
        elif page_id == "classes":
            self.stacked_widget.setCurrentIndex(1)
        elif page_id == "archive":
            self.stacked_widget.setCurrentIndex(2)
        
        self.set_active_nav_button(button)
    
    def set_active_nav_button(self, active_button):
        for btn in self.nav_buttons:
            if btn == active_button:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3d3d3d;
                        color: white;
                        text-align: left;
                        padding-left: 20px;
                        border: none;
                        font-size: 13px;
                        border-left: 4px solid #1e5631;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2d2d2d;
                        color: white;
                        text-align: left;
                        padding-left: 20px;
                        border: none;
                        font-size: 13px;
                    }
                    QPushButton:hover {
                        background-color: #3d3d3d;
                    }
                """)


def main():
    app = QApplication(sys.argv)
    window = ClassroomTaggingSystem()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()