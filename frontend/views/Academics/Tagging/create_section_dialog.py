import sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QGridLayout, QApplication, QSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Dict 
import logging 

logger = logging.getLogger(__name__)


class CreateSectionDialog(QDialog):
    def __init__(self, parent=None, section_data: Dict = None):
        """
            Initialize the Create/Edit Section dialog.

            Args:
                parent: Parent widget
                section_data: Existing section data for editing (None for create mode)
        """
        super().__init__(parent)

        # Store whether we're in edit mode
        self.is_edit_mode = section_data is not None
        self.section_data = section_data

        # Set window title based on mode
        title_text = "Edit Section" if self.is_edit_mode else "Create Section"
        self.setWindowTitle(title_text)

        # self.setFixedSize(480, 400)  # Larger height to avoid overlap
        self.setStyleSheet("""
            QLabel {
                color: #2d2d2d;
                font-size: 14px;
            }
            QLineEdit, QComboBox, QSpinBox{
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 6px 10px;
                background-color: #f9f9f9;
                min-width: 300px;
                min-height: 30px;
                font-size: 14px;
            }
            QComboBox QAbstractItemView {
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
                height: 5px;
            }
            QPushButton {
                background-color: #1e5631;
                color: white;
                padding: 8px 18px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
                border: none;
                min-width: 100px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #2d5a3d;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(5)

        # Title
        title = QLabel("Create Section")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))
        title.setStyleSheet("color: #1e5631; margin-bottom: 10px;")
        main_layout.addWidget(title)

        # Section input
        section_label = QLabel("Section")
        self.section_input = QLineEdit()
        main_layout.addWidget(section_label)
        main_layout.addWidget(self.section_input)

        # Program Title dropdown
        program_label = QLabel("Program Title")
        self.program_combo = QComboBox()
        self.program_combo.addItems([
            "BS Computer Science",
            "BS Information Technology",
            "BS Data Science"
            "BS Information Systems"
        ])
        main_layout.addWidget(program_label)
        main_layout.addWidget(self.program_combo)

        # Curriculum dropdown
        curriculum_label = QLabel("Curriculum")
        self.curriculum_combo = QComboBox()
        self.curriculum_combo.addItems(["2023-2024", "2022-2023", "2021-2022"])
        main_layout.addWidget(curriculum_label)
        main_layout.addWidget(self.curriculum_combo)

        # Grid layout for Year, Capacity, and Lecture
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setVerticalSpacing(10)

        year_label = QLabel("Year")
        self.year_combo = QComboBox()
        self.year_combo.addItems(["1st", "2nd", "3rd", "4th"])
        self.year_combo.setMaximumWidth(20)  # Different width for grid combobox
        grid_layout.addWidget(year_label, 0, 0)
        grid_layout.addWidget(self.year_combo, 1, 0)

        capacity_label = QLabel("Capacity")
        # self.capacity_input = QLineEdit()  
        self.capacity_input = QSpinBox()
        self.capacity_input.setMinimum(1)
        self.capacity_input.setMaximum(50)
        # # Different width for grid combobox
        grid_layout.addWidget(capacity_label, 0, 1)
        grid_layout.addWidget(self.capacity_input, 1, 1)

        type_label = QLabel("Type")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Lecture", "Laboratory"])
        self.type_combo.setMaximumWidth(40)  # Different width for grid combobox
        grid_layout.addWidget(type_label, 2, 0)
        grid_layout.addWidget(self.type_combo, 3, 0)

        # Remarks label
        remarks_label = QLabel("Remarks")
        self.remarks_combo = QComboBox()
        self.remarks_combo.addItems([
            "Regular",
            "Petition"
        ])
        grid_layout.addWidget(remarks_label, 2, 1)
        grid_layout.addWidget(self.remarks_combo, 3, 1)
        main_layout.addLayout(grid_layout)


        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        draft_btn = QPushButton("Draft")

        # Change button text based on mode
        action_btn = QPushButton("Update" if self.is_edit_mode else "Create")

        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(draft_btn)
        buttons_layout.addWidget(action_btn)
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

        # Populate fields if in edit mode
        if self.is_edit_mode and section_data:
            self._populate_fields(section_data)

        # Connect signals
        cancel_btn.clicked.connect(self.reject)
        action_btn.clicked.connect(self.accept)
        draft_btn.clicked.connect(self.handle_draft)

    def _populate_fields(self, section_data: Dict) -> None:
        """
        Populate form fields with existing section data for editing.

        Args:
            section_data: Dictionary containing section information
        """
        try:
            # Populate text fields
            if 'section' in section_data:
                self.section_input.setText(str(section_data['section']))

            # Populate combo boxes by finding and setting the index
            if 'program' in section_data:
                index = self.program_combo.findText(section_data['program'])
                if index >= 0:
                    self.program_combo.setCurrentIndex(index)

            if 'curriculum' in section_data:
                index = self.curriculum_combo.findText(section_data['curriculum'])
                if index >= 0:
                    self.curriculum_combo.setCurrentIndex(index)

            if 'year' in section_data:
                index = self.year_combo.findText(section_data['year'])
                if index >= 0:
                    self.year_combo.setCurrentIndex(index)

            if 'capacity' in section_data:
                self.capacity_input.setValue(int(section_data['capacity']))

            if 'type' in section_data:
                index = self.type_combo.findText(section_data['type'])
                if index >= 0:
                    self.type_combo.setCurrentIndex(index)

            if 'remarks' in section_data:
                index = self.remarks_combo.findText(section_data['remarks'])
                if index >= 0:
                    self.remarks_combo.setCurrentIndex(index)

            logger.info(f"Populated form fields for section: {section_data.get('section', 'Unknown')}")

        except Exception as e:
            logger.exception(f"Error populating section fields: {e}")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.ignore()
        else: 
            return super().keyPressEvent(event)

    def handle_draft(self):
        """Handle draft button clicked."""
        pass

    def get_data(self) -> Dict:
        """
        Retrieve section data from form fields.
        
        Returns:
            Dict: Section data dictionary with all fields
        """

        data = {
            "section": self.section_input.text(),
            "program": self.program_combo.currentText(),
            "curriculum": self.curriculum_combo.currentText(),
            "year": self.year_combo.currentText(),
            "capacity": self.capacity_input.value(),
            "type": self.type_combo.currentText(),
            "remarks": self.remarks_combo.currentText()
        }

        logger.debug(f"Section data collected: {data['section']}")
        return data 


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = CreateSectionDialog()
    dialog.exec()
    sys.exit(app.exec())
