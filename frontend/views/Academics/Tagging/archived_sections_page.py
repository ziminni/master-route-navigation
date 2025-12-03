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
from frontend.services.Academics.model.Academics.Tagging.section_table_model import SectionsTableModel
from frontend.controller.Academics.Tagging.sections_controller import SectionsController
from frontend.controller.Academics.controller_manager import ControllerManager

logger = logging.getLogger(__name__)


class ArchivedSectionsPage(QWidget):
    """
    Archived sections management page.

    Shows only archived sections with option to unarchive.
    """

    def __init__(self):
        super().__init__()

        # Use shared controller instance for signals, but our own model for this view
        manager = ControllerManager()
        self.controller = manager.get_sections_controller()
        
        # Create our own model for archived sections view
        self.model = SectionsTableModel()
        
        # Connect to archive signal to refresh when a section is archived
        self.controller.section_archived.connect(self.on_section_archived)

        self.init_ui()
        self.load_archived_sections()
        self._refresh_all_buttons()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header with title
        header_layout = QHBoxLayout()
        title = QLabel("Archived Sections")
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
        self.table.setObjectName("archivedSectionsTable")

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
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)  # Actions column
        self.table.setColumnWidth(8, 150)  # Actions
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
            index = self.model.index(row, 8)
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
            self.table.setIndexWidget(self.model.index(row, 8), button_widget)
    
    def on_section_archived(self, section_id):
        """
        Called when a section is archived from the main sections page.
        Refreshes the archived view to show the newly archived section.
        """
        logger.info(f"[ArchivedSectionsPage] Section archived, refreshing view")
        self.load_archived_sections()
        self._refresh_all_buttons()

    def load_archived_sections(self):
        """
        Load all archived sections.
        """
        try:
            archived_sections = self.controller.service.get_archived_sections()
            self.model.set_sections(archived_sections)
        except Exception as e:
            logger.exception(f"Error loading archived sections: {e}")

    def handle_unarchive(self, row: int) -> None:
        """
        Handle unarchive button click for a specific row.

        Args:
            row: Row index in the table
        """
        try:
            section_id = self.model.get_section_id(row)
            section_data = self.controller.get_section_by_id(section_id)

            if not section_data:
                logger.error(f"Section data not found for row {row}")
                return

            # Confirmation dialog
            reply = QMessageBox.question(
                self,
                "Confirm Unarchive",
                f"Are you sure you want to unarchive section '{section_data['section']}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                success = self.controller.handle_unarchive_section(section_id)

                if success:
                    QMessageBox.information(
                        self,
                        "Success",
                        "Section unarchived successfully!",
                        QMessageBox.StandardButton.Ok
                    )
                    # Reload the archived sections
                    self.load_archived_sections()
                else:
                    QMessageBox.warning(
                        self,
                        "Unarchive Failed",
                        "Failed to unarchive the section."
                    )

        except Exception as e:
            logger.exception(f"Error unarchiving section at row {row}: {e}")
    
    def handle_unarchive_all(self) -> None:
        """
        Handle unarchive all button click.
        Unarchives all archived sections.
        """
        try:
            # Check if there are any archived sections
            if self.model.rowCount() == 0:
                QMessageBox.information(
                    self,
                    "No Archived Sections",
                    "There are no archived sections to unarchive.",
                    QMessageBox.StandardButton.Ok
                )
                return
            
            # Confirmation dialog
            reply = QMessageBox.question(
                self,
                "Confirm Unarchive All",
                f"Are you sure you want to unarchive all {self.model.rowCount()} archived section(s)?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                total_sections = 0
                failed_sections = []
                
                # Get all archived sections
                archived_sections = self.controller.service.get_archived_sections()
                
                # Unarchive each section
                for section_data in archived_sections:
                    success = self.controller.handle_unarchive_section(section_data['id'])
                    if success:
                        total_sections += 1
                    else:
                        failed_sections.append(section_data['section'])
                
                # Show results
                if failed_sections:
                    QMessageBox.warning(
                        self,
                        "Partial Success",
                        f"Unarchived {total_sections} section(s).\n\n"
                        f"Failed to unarchive: {', '.join(failed_sections)}",
                        QMessageBox.StandardButton.Ok
                    )
                else:
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Successfully unarchived all {total_sections} section(s)!",
                        QMessageBox.StandardButton.Ok
                    )
                
                # Reload the archived sections
                self.load_archived_sections()
                self._refresh_all_buttons()
        
        except Exception as e:
            logger.exception(f"Error handling unarchive all: {e}")
            QMessageBox.critical(
                self,
                "Error",
                "An unexpected error occurred while unarchiving sections."
            )
