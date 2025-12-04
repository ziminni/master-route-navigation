import logging

from PyQt6.QtWidgets import (QWidget,
                             QVBoxLayout,
                             QHBoxLayout,
                             QPushButton,
                             QLabel,
                             QTableView,
                             QHeaderView,
                             QMessageBox)
from PyQt6.QtGui import QFont
from frontend.services.Academics.model.Academics.Tagging.classes_table_model import ClassesTableModel
from frontend.controller.Academics.Tagging.classes_controller import ClassesController
from frontend.controller.Academics.controller_manager import ControllerManager

logger = logging.getLogger(__name__)


class ArchivedClassesPage(QWidget):
    """
    Archived classes management page.

    Shows only archived classes with option to unarchive.
    """

    def __init__(self):
        super().__init__()

        # Use shared controller instance for signals, but our own model for this view
        manager = ControllerManager()
        self.controller = manager.get_classes_controller()
        
        # Create our own model for archived classes view
        self.model = ClassesTableModel()
        
        # Connect to archive signal to refresh when a class is archived
        self.controller.class_archived.connect(self.on_class_archived)

        self.init_ui()
        self.load_archived_classes()
        self._refresh_all_buttons()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header with title
        header_layout = QHBoxLayout()
        title = QLabel("Archived Classes")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))
        title.setStyleSheet("color: #2d2d2d;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Unarchive All button
        self.unarchive_all_btn = QPushButton("Unarchive All")
        self.unarchive_all_btn.setFixedHeight(40)
        self.unarchive_all_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.unarchive_all_btn.clicked.connect(self.handle_unarchive_all)
        header_layout.addWidget(self.unarchive_all_btn)
        
        layout.addLayout(header_layout)

        # Table
        self.table = QTableView()
        self.table.setObjectName("archivedClassesTable")

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
                background-color: #6c757d;
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
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.resizeColumnsToContents()
        header.setMinimumSectionSize(50)
        self.table.setColumnWidth(0, max(50, self.table.columnWidth(0)))  # No.
        self.table.setColumnWidth(1, max(80, self.table.columnWidth(1)))  # Code
        self.table.setColumnWidth(2, max(200, self.table.columnWidth(2)))  # Title
        self.table.setColumnWidth(3, max(60, self.table.columnWidth(3)))  # Units
        self.table.setColumnWidth(4, max(80, self.table.columnWidth(4)))  # Section
        self.table.setColumnWidth(5, max(150, self.table.columnWidth(5)))  # Schedule
        self.table.setColumnWidth(6, max(100, self.table.columnWidth(6)))  # Room
        self.table.setColumnWidth(7, max(150, self.table.columnWidth(7)))  # Instructor
        self.table.setColumnWidth(8, max(80, self.table.columnWidth(8)))  # Type
        self.table.setColumnWidth(9, 150)  # Actions

        self.table.verticalHeader().setDefaultSectionSize(60)

        layout.addWidget(self.table)
        self.setLayout(layout)

        # Connect signals
        self._connect_signals()

    def _connect_signals(self) -> None:
        """
        Connect page signals to its appropriate slots.
        """
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
            QWidget containing only unarchive button
        """
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(4, 4, 4, 4)
        button_layout.setSpacing(4)

        # Unarchive button
        unarchive_btn = QPushButton("Unarchive")
        unarchive_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        unarchive_btn.clicked.connect(lambda checked, btn=unarchive_btn: self._handle_unarchive_clicked(btn))

        button_layout.addWidget(unarchive_btn)
        button_layout.addStretch()

        return button_widget

    def _handle_unarchive_clicked(self, button: QPushButton) -> None:
        """
        Handle unarchive button click by finding the row from the button's position.

        Args:
            button: The unarchive button that was clicked
        """
        # Find which row this button belongs to
        for row in range(self.model.rowCount()):
            index = self.model.index(row, 9)
            widget = self.table.indexWidget(index)
            if widget and button in widget.findChildren(QPushButton):
                self.handle_unarchive(row)
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
    
    def on_class_archived(self, class_id):
        """
        Called when a class is archived from the main classes page.
        Refreshes the archived view to show the newly archived class.
        """
        logger.info(f"[ArchivedClassesPage] Class archived, refreshing view")
        self.load_archived_classes()
        self._refresh_all_buttons()

    def load_archived_classes(self):
        """
        Load all archived classes.
        """
        try:
            archived_classes = self.controller.service.get_archived_classes()
            self.model.set_classes(archived_classes)
        except Exception as e:
            logger.exception(f"Error loading archived classes: {e}")

    def handle_unarchive(self, row: int) -> None:
        """
        Handle unarchive button click for a specific row.

        Args:
            row: Row index in the table
        """
        try:
            class_id = self.model.get_class_id(row)
            class_data = self.controller.get_class_by_id(class_id)

            if not class_data:
                logger.error(f"Class data not found for row {row}")
                return

            # Confirmation dialog
            reply = QMessageBox.question(
                self,
                "Confirm Unarchive",
                f"Are you sure you want to unarchive class '{class_data['code']} - {class_data['title']}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                success, message, sections_count = self.controller.handle_unarchive_class(class_id)

                if success:
                    QMessageBox.information(
                        self,
                        "Success",
                        message,
                        QMessageBox.StandardButton.Ok
                    )
                    # Reload the archived classes
                    self.load_archived_classes()
                    self._refresh_all_buttons()
                else:
                    QMessageBox.warning(
                        self,
                        "Unarchive Failed",
                        message
                    )

        except Exception as e:
            logger.exception(f"Error unarchiving class at row {row}: {e}")
    
    def handle_unarchive_all(self) -> None:
        """
        Handle unarchive all button click.
        Unarchives all archived classes and their associated sections.
        """
        try:
            # Check if there are any archived classes
            if self.model.rowCount() == 0:
                QMessageBox.information(
                    self,
                    "No Archived Classes",
                    "There are no archived classes to unarchive.",
                    QMessageBox.StandardButton.Ok
                )
                return
            
            # Confirmation dialog
            reply = QMessageBox.question(
                self,
                "Confirm Unarchive All",
                f"Are you sure you want to unarchive all {self.model.rowCount()} archived class(es)?\n\n"
                "This will also unarchive all associated sections.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                total_classes = 0
                total_sections = 0
                failed_classes = []
                
                # Get all archived classes
                archived_classes = self.controller.service.get_archived_classes()
                
                # Unarchive each class
                for class_data in archived_classes:
                    success, message, sections_count = self.controller.handle_unarchive_class(class_data['id'])
                    if success:
                        total_classes += 1
                        total_sections += sections_count
                    else:
                        failed_classes.append(class_data['code'])
                
                # Show results
                if failed_classes:
                    QMessageBox.warning(
                        self,
                        "Partial Success",
                        f"Unarchived {total_classes} class(es) and {total_sections} section(s).\n\n"
                        f"Failed to unarchive: {', '.join(failed_classes)}",
                        QMessageBox.StandardButton.Ok
                    )
                else:
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Successfully unarchived all {total_classes} class(es) and {total_sections} section(s)!",
                        QMessageBox.StandardButton.Ok
                    )
                
                # Reload the archived classes
                self.load_archived_classes()
                self._refresh_all_buttons()
        
        except Exception as e:
            logger.exception(f"Error handling unarchive all: {e}")
            QMessageBox.critical(
                self,
                "Error",
                "An unexpected error occurred while unarchiving classes."
            )
