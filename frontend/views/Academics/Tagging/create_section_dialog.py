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
        self._is_initializing = True # flag to prevent autofill everytime dialog is opened

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
        section_label = QLabel("Name")
        self.section_input = QLineEdit()
        self.section_input.setPlaceholderText("A")
        main_layout.addWidget(section_label)
        main_layout.addWidget(self.section_input)

        # Program Title dropdown
        program_label = QLabel("Program Title")
        self.program_combo = QComboBox()
        self.program_combo.addItems([
            "BS Information Technology",
            "BS Data Science",
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

        # Curriculum dropdown
        track_label = QLabel("Track")
        self.track_combo = QComboBox()
        self.track_combo.addItems(["N/A", "Data Networking", "Information Management", "Software Development"])
        main_layout.addWidget(track_label)
        main_layout.addWidget(self.track_combo)

        # Grid layout for Year, Capacity, and Lecture
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setVerticalSpacing(10)

        year_label = QLabel("Year")
        self.year_combo = QComboBox()
        self.year_combo.addItems(["1st", "2nd", "3rd", "4th", "N/A (Petition)"])
        self.year_combo.setMaximumWidth(20)  # Different width for grid combobox
        grid_layout.addWidget(year_label, 0, 0)
        grid_layout.addWidget(self.year_combo, 1, 0)

        capacity_label = QLabel("Capacity")
        # self.capacity_input = QLineEdit()  
        self.capacity_input = QSpinBox()
        self.capacity_input.setMinimum(1)
        self.capacity_input.setMaximum(50)
        self.capacity_input.setValue(50)
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
        action_btn.clicked.connect(self.handle_create_or_update)
        draft_btn.clicked.connect(self.handle_draft)

        # for fields with dynamic default values based on other field values
        self.type_combo.currentTextChanged.connect(self._handle_type_changed)
        self.remarks_combo.currentTextChanged.connect(self._handle_remarks_changed)

        # Populate fields if in edit mode
        if self.is_edit_mode and section_data:
            self._populate_fields(section_data)

        self._is_initializing = False

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

    def _validate_input(self) -> tuple[bool, str]:
        """
        Validate user input before creating/updating section.

        Returns:
            tuple: (is_valid, error_message)
        """
        section = self.section_input.text().strip().upper()
        remarks = self.remarks_combo.currentText().strip()

        # Check if section field is empty
        if not section:
            return False, "Section field cannot be empty."

        if remarks == "Regular":
            # Check if section contains only a single letter
            if not section.isalpha() or len(section) != 2:
                if len(section) == 2 and section[1] != "X":
                    return False, "Section field must follow format (e.g.,'A', 'Ax', 'B', 'Bx')."
                return False, "Section field must follow format (e.g.,'A', 'Ax', 'B', 'Bx')."
        elif remarks == "Petition":
            # Assume petition section names are 'PS99', 'PS100', etc.
            valid_start = section[0:2]
            if valid_start != "PS":
                return False, "Invalid section name format, must start with 'PS'."
            if len(section) > 5:
                return False, "Invalid section field length."

        return True, ""

    def _handle_type_changed(self, type_value:str) -> None:
        """
        Handle type change to automatically set default capacity.
        Only applies during user interaction, not during initialization.

        Args:
            type_value: The selected type (Lecture/Laboratory)
        """
        # Don't override capacity during initialization or edit mode
        if self._is_initializing:
            return

        if type_value == "Lecture":
            self.capacity_input.setValue(50)
        elif type_value == "Laboratory":
            self.capacity_input.setValue(25)

    def _handle_remarks_changed(self, remarks: str) -> None:
        """
        Handle remarks change to provide hint or validation.

        Args:
            remarks: The selected remarks (Regular/Petition)
        """
        if self._is_initializing:
            return


        if remarks == "Petition":
            # Clear input
            if self.section_input.text() and len(self.section_input.text()) == 1:
                self.section_input.clear()  # Clear single letter if switching to Petition
            self.section_input.setPlaceholderText("PS99")

            self.year_combo.setCurrentIndex(4)
        elif remarks == "Regular":
            # Clear if not matching Regular format
            current_text = self.section_input.text()
            if current_text and (not current_text.isalpha() or len(current_text) != 1):
                self.section_input.clear()
            self.section_input.setPlaceholderText("A")
            self.year_combo.setCurrentIndex(0)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.ignore()
        else: 
            return super().keyPressEvent(event)

    def handle_draft(self):
        """Handle draft button clicked."""
        pass

    def handle_create_or_update(self):
        """Handle create/update button click with validation."""
        from PyQt6.QtWidgets import QMessageBox

        is_valid, error_message = self._validate_input()

        if not is_valid:
            QMessageBox.warning(
                self,
                "Invalid Input",
                error_message,
                QMessageBox.StandardButton.Ok
            )
            return  # Don't close dialog

        self.accept()  # Close dialog with success

    def get_data(self) -> Dict:
        """
        Retrieve section data from form fields.
        
        Returns:
            Dict: Section data dictionary with all fields
        """

        section = self.section_input.text().strip().lower()
        if len(section) == 2:
            section = f"{section[0].upper()}{section[1]}"
        else:
            section = f"{section[0]}"

        data = {
            "section": section,
            "program": self.program_combo.currentText(),
            "curriculum": self.curriculum_combo.currentText(),
            "track": self.track_combo.currentText(),
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
