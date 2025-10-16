import logging

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QTableView,
                             QStackedWidget, QComboBox, QHeaderView)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QFont, QIcon, QColor

from frontend.controller.Academics.Tagging.classes_controller import ClassesController
from frontend.controller.Academics.controller_manager import ControllerManager
from frontend.services.Academics.Tagging.section_service import SectionService
from frontend.services.Academics.model.Academics.Tagging.classes_table_model import ClassesTableModel
from .create_class_dialog import CreateClassDialog

logger = logging.getLogger(__name__)


class ClassesPage(QWidget):
    def __init__(self):
        super().__init__()

        self.section_service = SectionService()
        # self.controller = ClassesController()
        manager = ControllerManager()
        self.controller = manager.get_classes_controller()

        self.model = ClassesTableModel()
        self.controller.set_model(self.model)

        self.init_ui()
        self.controller.load_classes()

        # Refresh buttons after data is loaded
        self._refresh_all_buttons()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        title = QLabel("Classes (First Semester, A.Y. 2025-2026)")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))
        title.setStyleSheet("color: #2d2d2d;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Sort by dropdown
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Sort by", "Code", "Title", "Section"])
        self.sort_combo.setStyleSheet("""
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
        header_layout.addWidget(self.sort_combo)
        
        # Add Class button
        self.add_btn = QPushButton("Add Class")
        self.add_btn.setStyleSheet("""
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
        header_layout.addWidget(self.add_btn)
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableView()
        self.table.setObjectName("classesTable")
        
        # Sample data
        data = [
            {'no': 1, 'code': 'IT57', 'title': 'Fundamentals of Database', 
             'units': 3, 'section': '3A', 'schedule': 'TTH 7:00 - 7:30 AM',
             'room': 'CISC Room 3', 'instructor': 'Juan Dela Cruz', 'type': 'Regular'},
            {'no': 2, 'code': 'CS101', 'title': 'Introduction to Programming', 
             'units': 3, 'section': '1A', 'schedule': 'MW 9:00 - 10:30 AM',
             'room': 'CISC Room 1', 'instructor': 'Maria Santos', 'type': 'Regular'}
        ]

        self.table.setModel(self.model)
        
        # Table styling
        self.table.setStyleSheet("""
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
        
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setMinimumSectionSize(100)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableView.SelectionMode.NoSelection)

        
        # Set reasonable column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.resizeColumnsToContents()
        header.setMinimumSectionSize(50)
        self.table.setColumnWidth(0, max(50, self.table.columnWidth(0)))  # No. - at least 50px
        self.table.setColumnWidth(1, max(80, self.table.columnWidth(1)))  # Code - at least 80px
        self.table.setColumnWidth(2, max(200, self.table.columnWidth(2)))  # Title - at least 200px
        self.table.setColumnWidth(3, max(60, self.table.columnWidth(3)))  # Units - at least 60px
        self.table.setColumnWidth(4, max(80, self.table.columnWidth(4)))  # Section - at least 80px
        self.table.setColumnWidth(5, max(150, self.table.columnWidth(5)))  # Schedule - at least 150px
        self.table.setColumnWidth(6, max(100, self.table.columnWidth(6)))  # Room - at least 100px
        self.table.setColumnWidth(7, max(150, self.table.columnWidth(7)))  # Instructor - at least 150px
        self.table.setColumnWidth(8, max(80, self.table.columnWidth(8)))  # Type - at least 80px
        self.table.setColumnWidth(9, 150)

        # Actions - fixed at 150px
        # # header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        # header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        # header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        # header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        # header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        # header.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        #
        # header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        # header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        # header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        #
        # self.table.setColumnWidth(0, 10)  # No.
        # self.table.setColumnWidth(1, 60)  # Code
        # self.table.setColumnWidth(2, 200) # Title
        # self.table.setColumnWidth(3, 30)  # Units
        # self.table.setColumnWidth(4, 60)  # Section
        # self.table.setColumnWidth(5, 120) # Schedule
        # self.table.setColumnWidth(6, 60) # Room
        # self.table.setColumnWidth(7, 150) # Instructor
        # self.table.setColumnWidth(8, 80) # Type
        # self.table.setColumnWidth(9, 150)  # Actions

        self.table.verticalHeader().setDefaultSectionSize(60)

        layout.addWidget(self.table)
        self.setLayout(layout)

        self._connect_signals()

    def _connect_signals(self) -> None:
        """
        Connect page signals to its appropriate slots.
        """
        self.add_btn.clicked.connect(self.handle_add)

        # Connect model signals to refresh action buttons
        self.model.rowsInserted.connect(self._on_rows_changed)
        self.model.modelReset.connect(self._refresh_all_buttons)

    def _create_action_buttons(self, row: int) -> QWidget:
        """
        Create action buttons widget for a specific row.

        Args:
            row: Row index to create buttons for

        Returns:
            QWidget containing edit and delete buttons
        """
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(4, 4, 4, 4)
        button_layout.setSpacing(4)

        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #2d2d2d;
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #ffcd38;
            }
        """)
        edit_btn.clicked.connect(lambda checked, btn=edit_btn: self._handle_edit_clicked(btn))

        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        delete_btn.clicked.connect(lambda checked, btn=delete_btn: self._handle_delete_clicked(btn))

        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()

        return button_widget

    def _handle_edit_clicked(self, button: QPushButton) -> None:
        """
        Handle edit button click by finding the row from the button's position.

        Args:
            button: The edit button that was clicked
        """
        # Find which row this button belongs to
        for row in range(self.model.rowCount()):
            index = self.model.index(row, 9)
            widget = self.table.indexWidget(index)
            if widget and button in widget.findChildren(QPushButton):
                self.handle_edit(row)
                return

    def _handle_delete_clicked(self, button: QPushButton) -> None:
        """
        Handle delete button click by finding the row from the button's position.

        Args:
            button: The delete button that was clicked
        """
        # Find which row this button belongs to
        for row in range(self.model.rowCount()):
            index = self.model.index(row, 9)
            widget = self.table.indexWidget(index)
            if widget and button in widget.findChildren(QPushButton):
                self.handle_delete(row)
                return

    def _on_rows_changed(self):
        """
        Called when rows are inserted into the model.
        Refreshes action buttons for all rows.
        """
        self._refresh_all_buttons()

    def _refresh_all_buttons(self):
        """
        Refresh action buttons for all rows in the table.
        """
        for row in range(self.model.rowCount()):
            button_widget = self._create_action_buttons(row)
            self.table.setIndexWidget(self.model.index(row, 9), button_widget)

    # =========================================================================
    # CRUD OPERATIONS
    # =========================================================================


    def handle_add(self) -> None:
        """
        Handle add button click.

        Data Flow:
        1. Open CreateClassDialog
        2. If user clicks Create:
           → Get data from dialog
           → Pass to controller
           → Controller validates and calls service
           → Controller updates model
           → View automatically refreshes
        """
        logger.info("Entered handled_add method")
        try:
            while True:
                sections = self.section_service.get_all()
                logger.info(f"Sections: {sections}")
                dialog = CreateClassDialog(self, sections)

                if dialog.exec():
                    success, error_message = self.controller.handle_create_class(dialog)

                    if success:
                        # Class created successfully, exit loop
                        from PyQt6.QtWidgets import QMessageBox
                        QMessageBox.information(
                            self,
                            "Success",
                            "Class created successfully!",
                            QMessageBox.StandardButton.Ok
                        )
                        break
                    else:
                        # Show error dialog and keep the create dialog open
                        from PyQt6.QtWidgets import QMessageBox
                        reply = QMessageBox.critical(
                            self,
                            "Error Creating Class",
                            f"{error_message}\n\nWould you like to modify the class details?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.Yes
                        )

                        if reply == QMessageBox.StandardButton.No:
                            # User doesn't want to fix, exit loop
                            break
                            # If Yes, loop continues and dialog reopens
                else:
                    # User cancelled
                    break

        except Exception as e:
            logger.exception(f"An error occured while creating a class: {e}")

    def handle_edit(self, row: int) -> None:
        """
        Handle edit button click for a specific row.

        Args:
            row: Row index in the table
        """
        # try:
        #     class_id = self.model.get_class_id(row)
        #     class_data = self.controller.get_class_by_id(class_id)
        #
        #     if not class_data:
        #         logger.error(f"Class data not found for row {row}")
        #         return
        #
        #     sections = self.section_service.get_all()
        #     dialog = CreateClassDialog(self, sections, class_data)
        #     dialog.setWindowTitle("Edit Class")
        #
        #     if dialog.exec():
        #         updated_data = dialog.get_data()
        #         success = self.controller.handle_update_class(class_id, updated_data)
        #
        #         if success:
        #             self._refresh_row_buttons(row)
        #
        # except Exception as e:
        #     logger.exception(f"Error editing class at row {row}: {e}")

        # Get data directly from model
        try:
            class_data = self.model.get_class_data(row)

            if not class_data:
                logger.error(f"Class data not found for row {row}")
                return

            class_id = class_data.get('id')
            logger.info(f"Editing class ID {class_id} from row {row}")

            sections = self.section_service.get_all()
            dialog = CreateClassDialog(self, sections, class_data)
            dialog.setWindowTitle("Edit Class")

            while True:  # Loop to allow user to fix conflicts
                if dialog.exec():
                    updated_data = dialog.get_data()
                    success, error_message = self.controller.handle_update_class(class_id, updated_data)

                    if success:
                        self._refresh_row_buttons(row)
                        from PyQt6.QtWidgets import QMessageBox
                        QMessageBox.information(
                            self,
                            "Success",
                            "Class updated successfully!",
                            QMessageBox.StandardButton.Ok
                        )
                        break
                    else:
                        # Show error dialog
                        from PyQt6.QtWidgets import QMessageBox
                        reply = QMessageBox.critical(
                            self,
                            "Error Updating Class",
                            f"{error_message}\n\nWould you like to modify the class details?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.Yes
                        )

                        if reply == QMessageBox.StandardButton.No:
                            break
                        # If Yes, loop continues
                else:
                    # User cancelled
                    break

        except Exception as e:
            logger.exception(f"Error editing class at row {row}: {e}")

    def handle_delete(self, row: int) -> None:
        """
        Handle delete button click for a specific row.

        Args:
            row: Row index in the table
        """
        try:
            from PyQt6.QtWidgets import QMessageBox

            class_id = self.model.get_class_id(row)
            class_data = self.controller.get_class_by_id(class_id)

            if not class_data:
                logger.error(f"Class data not found for row {row}")
                return

            # Confirmation dialog
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete class '{class_data['code']} - {class_data['title']}'?\n"
                f"This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                success = self.controller.handle_delete_class(class_id)

                if not success:
                    QMessageBox.warning(
                        self,
                        "Delete Failed",
                        "Failed to delete the class. Please try again."
                    )

        except Exception as e:
            logger.exception(f"Error deleting class at row {row}: {e}")

    def _refresh_row_buttons(self, row: int) -> None:
        """
        Refresh the action buttons for a specific row after update.

        Args:
            row: Row index to refresh
        """
        button_widget = self._create_action_buttons(row)
        self.table.setIndexWidget(self.model.index(row, 9), button_widget)

