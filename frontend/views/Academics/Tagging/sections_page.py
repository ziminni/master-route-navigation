import logging

from PyQt6.QtWidgets import (QApplication,
                             QMainWindow, 
                             QWidget, 
                             QVBoxLayout, 
                             QHBoxLayout, 
                             QPushButton, 
                             QLabel, 
                             QTableView,
                             QHeaderView)
from PyQt6.QtGui import QFont
from frontend.services.Academics.model.Academics.Tagging.section_table_model import SectionsTableModel
from frontend.views.Academics.Tagging.create_section_dialog import CreateSectionDialog
from frontend.controller.Academics.Tagging.sections_controller import SectionsController
from frontend.controller.Academics.controller_manager import ControllerManager

logger = logging.getLogger(__name__)

class SectionsPage(QWidget):
    """
    Complete sections management page with full CRUD functionality.

    Flow:
    User interacts with this page
        → Page calls Controller methods
        → Controller calls Service methods
        → Controller updates Model
        → Model notifies View (automatic Qt signals)
        → View refreshes display
    """

    def __init__(self):
        super().__init__()

        # Use shared controller instance via ControllerManager
        manager = ControllerManager()
        self.controller = manager.get_sections_controller()
        self.model = SectionsTableModel()
        self.controller.set_model(self.model)
        
        # Connect to signals to refresh when sections are archived/unarchived
        self.controller.section_unarchived.connect(self.on_section_unarchived)
        self.controller.section_archived.connect(self.on_section_archived)
        
        self.init_ui()
        self.controller.load_sections()

        self._refresh_all_buttons()


    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header with title and add button
        header_layout = QHBoxLayout()
        title = QLabel("Sections (First Semester, A.Y. 2025-2026)")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))
        title.setStyleSheet("color: #2d2d2d;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.add_btn = QPushButton("Add Section")
        self.add_btn.setFixedHeight(40)
        self.add_btn.setStyleSheet("""
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

        self.archive_btn = QPushButton("Archive All")
        self.archive_btn.setFixedHeight(40)
        self.archive_btn.setStyleSheet("""
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

        header_layout.addWidget(self.add_btn)
        header_layout.addWidget(self.archive_btn)
        layout.addLayout(header_layout)

        # Table
        self.table = QTableView()
        self.table.setObjectName("sectionsTable")

        # Set model
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
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setMinimumSectionSize(100)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)


        # Set reasonable column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)  # Actions column (now index 8)
        self.table.setColumnWidth(8, 250)  # Actions - wider to fit all buttons
        self.table.setColumnWidth(0, 60)   # No.
        self.table.setColumnWidth(1, 80)   # Section
        self.table.setColumnWidth(2, 200)  # Program
        self.table.setColumnWidth(3, 150)  # Track
        self.table.setColumnWidth(4, 60)   # Year
        self.table.setColumnWidth(5, 100)  # Type
        self.table.setColumnWidth(6, 80)   # Capacity

        self.table.verticalHeader().setDefaultSectionSize(60)

        layout.addWidget(self.table)
        self.setLayout(layout)

        # connect signals to slots
        self._connect_signals()

    def _connect_signals(self) -> None:
        """
        Connect page signals to its appropriate slots.
        """
        self.add_btn.clicked.connect(self.handle_add)
        self.archive_btn.clicked.connect(self.handle_archive_all)

        # Connect model signals to refresh action buttons
        self.model.rowsInserted.connect(self._on_rows_changed)
        self.model.modelReset.connect(self._refresh_all_buttons)
        self.model.rowsRemoved.connect(self._refresh_all_buttons)
        self.model.dataLoaded.connect(self._refresh_all_buttons)


    def _create_action_buttons(self, row: int) -> QWidget:
        """
        Create action buttons widget for a specific row.

        Args:
            row: Row index to create buttons for

        Returns:
            QWidget containing edit, delete, and archive buttons
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

        # Archive button
        archive_btn = QPushButton("Archive")
        archive_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        archive_btn.clicked.connect(lambda checked, btn=archive_btn: self._handle_archive_clicked(btn))

        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(archive_btn)
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
            index = self.model.index(row, 8)
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
            index = self.model.index(row, 8)
            widget = self.table.indexWidget(index)
            if widget and button in widget.findChildren(QPushButton):
                self.handle_delete(row)
                return

    def _handle_archive_clicked(self, button: QPushButton) -> None:
        """
        Handle archive button click by finding the row from the button's position.

        Args:
            button: The archive button that was clicked
        """
        # Find which row this button belongs to
        for row in range(self.model.rowCount()):
            index = self.model.index(row, 8)
            widget = self.table.indexWidget(index)
            if widget and button in widget.findChildren(QPushButton):
                self.handle_archive(row)
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
            self.table.setIndexWidget(self.model.index(row, 8), button_widget)
    
    def on_section_unarchived(self, section_data):
        """
        Called when a section is unarchived from the archived sections page.
        Refreshes the view to show the unarchived section.
        """
        logger.info(f"[SectionsPage] Section unarchived, refreshing view")
        self.controller.load_sections()
        self._refresh_all_buttons()

    def on_section_archived(self, section_id):
        """
        Called when a section is archived from this page.
        Refreshes the view to remove the archived section.
        """
        logger.info(f"[SectionsPage] Section {section_id} archived, refreshing view")
        self.controller.load_sections()
        self._refresh_all_buttons()

    def load_sections(self):
        pass 

    # =========================================================================
    # CRUD OPERATIONS  
    # =========================================================================

    def handle_add(self) -> None:
        """
        Handle add button click.
        
        Data Flow:
        1. Open CreateSectionDialog
        2. If user clicks Create:
           → Get data from dialog
           → Pass to controller
           → Controller validates and calls service
           → Controller updates model
           → View automatically refreshes
        """
        from PyQt6.QtWidgets import QMessageBox
        dialog = CreateSectionDialog(self)

        while True:  # Loop to allow user to fix duplicate issues
            if dialog.exec():
                success, error_message = self.controller.handle_create_section(dialog)

                if success:
                    # Section created successfully
                    QMessageBox.information(
                        self,
                        "Success",
                        "Section created successfully!",
                        QMessageBox.StandardButton.Ok
                    )
                    break
                else:
                    # Show error dialog with the duplicate information
                    reply = QMessageBox.critical(
                        self,
                        "Error Creating Section",
                        f"{error_message}\n\nWould you like to modify the section details?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )

                    if reply == QMessageBox.StandardButton.No:
                        # User doesn't want to fix, exit loop
                        break
                        # If Yes, dialog will reopen with same data for editing
            else:
                # User cancelled
                break


    def handle_edit(self, row: int) -> None:
        """
        Handle edit button click for a specific row.

        Args:
            row: Row index in the table
        """
        try:
            from PyQt6.QtWidgets import QMessageBox

            section_id = self.model.get_section_id(row)

            # Check if section can be edited
            can_edit, error_message = self.controller.can_edit_section(section_id)
            if not can_edit:
                QMessageBox.warning(
                    self,
                    "Cannot Edit Section",
                    error_message,
                    QMessageBox.StandardButton.Ok
                )
                return

            section_data = self.controller.get_section_by_id(section_id)

            if not section_data:
                logger.error(f"Section data not found for row {row}")
                return

            dialog = CreateSectionDialog(self, section_data)
            dialog.setWindowTitle("Edit Section")

            while True:  # Loop to allow user to fix duplicate issues
                if dialog.exec():
                    updated_data = dialog.get_data()
                    success, error_message = self.controller.handle_update_section(section_id, updated_data)

                    if success:
                        # Refresh the row buttons
                        self._refresh_row_buttons(row)
                        QMessageBox.information(
                            self,
                            "Success",
                            "Section updated successfully!",
                            QMessageBox.StandardButton.Ok
                        )
                        break
                    else:
                        # Show error dialog
                        reply = QMessageBox.critical(
                            self,
                            "Error Updating Section",
                            f"{error_message}\n\nWould you like to modify the section details?",
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
            logger.exception(f"Error editing section at row {row}: {e}")

    def handle_delete(self, row: int) -> None:
        """
        Handle delete button click for a specific row.

        Args:
            row: Row index in the table
        """
        try:
            from PyQt6.QtWidgets import QMessageBox

            section_id = self.model.get_section_id(row)
            section_data = self.controller.get_section_by_id(section_id)

            if not section_data:
                logger.error(f"Section data not found for row {row}")
                return

            # Confirmation dialog
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete section '{section_data['section']}'?\n"
                f"This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                success = self.controller.handle_delete_section(section_id)

                if not success:
                    QMessageBox.warning(
                        self,
                        "Delete Failed",
                        "Failed to delete the section. Section has associated classes."
                    )

        except Exception as e:
            logger.exception(f"Error deleting section at row {row}: {e}")

    def _refresh_row_buttons(self, row: int) -> None:
        """
        Refresh the action buttons for a specific row after update.

        Args:
            row: Row index to refresh
        """
        button_widget = self._create_action_buttons(row)
        self.table.setIndexWidget(self.model.index(row, 8), button_widget)

    def handle_archive(self, row: int) -> None:
        """
        Handle archive button click for a specific row.

        Args:
            row: Row index in the table
        """
        try:
            from PyQt6.QtWidgets import QMessageBox

            section_id = self.model.get_section_id(row)
            section_data = self.controller.get_section_by_id(section_id)

            if not section_data:
                logger.error(f"Section data not found for row {row}")
                return

            # Confirmation dialog
            reply = QMessageBox.question(
                self,
                "Confirm Archive",
                f"Are you sure you want to archive section '{section_data['section']}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                success, error_message = self.controller.handle_archive_section(section_id)

                if not success:
                    QMessageBox.warning(
                        self,
                        "Archive Failed",
                        error_message or "Failed to archive the section."
                    )
                else:
                    QMessageBox.information(
                        self,
                        "Success",
                        "Section archived successfully!",
                        QMessageBox.StandardButton.Ok
                    )

        except Exception as e:
            logger.exception(f"Error archiving section at row {row}: {e}")

    def handle_archive_all(self) -> None:
        """
        Handle archive all button click.
        """
        try:
            from PyQt6.QtWidgets import QMessageBox

            # Confirmation dialog
            reply = QMessageBox.question(
                self,
                "Confirm Archive All",
                "Are you sure you want to archive all sections?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                success, error_message = self.controller.handle_archive_all_sections()

                if not success:
                    QMessageBox.warning(
                        self,
                        "Archive Failed",
                        error_message or "Failed to archive all sections."
                    )
                else:
                    QMessageBox.information(
                        self,
                        "Success",
                        "All sections archived successfully!",
                        QMessageBox.StandardButton.Ok
                    )

        except Exception as e:
            logger.exception(f"Error archiving all sections: {e}")

    def handle_refresh(self):
        pass 