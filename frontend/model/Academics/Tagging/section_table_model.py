from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSignal
from PyQt6.QtGui import QColor
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class SectionsTableModel(QAbstractTableModel):
    dataLoaded = pyqtSignal()

    def __init__(self, parent=None):
        """
        Initialize the sections table model. 

        Args:
            parent: Parent object (optional)
        """

        super().__init__()
        self._sections: List[Dict] = []
        self._headers = [
            "No.",
            "Section",
            "Program",
            "Track",
            "Year",
            "Type",
            "Capacity",
            "Remarks",
            "Actions"
        ]

        logging.info("Initialized section table model")

    # def load_data(self):
    #     self.beginResetModel()
    #     self._sections = self._service.get_sections()
    #     self.endResetModel()

    def rowCount(self, parent=None):
        return len(self._sections)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None

        # Actions column (index 8) contains widgets, not data
        if index.column() == 8:
            return None

        section = self._sections[index.row()]
        keys = ["id", "section", "program", "track", "year", "type", "capacity", "remarks"]
        return section.get(keys[index.column()], "")
    
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
    

    # ========================================================
    # DATA MANAGEMENT METHODS
    # ========================================================

    def add_section(self, section: Dict) -> None:
        logger.debug(f"Entered add_section method")

        section_row = len(self._sections)

        # notify view of row insertion
        self.beginInsertRows(QModelIndex(), section_row, section_row)
        self._sections.append(section)
        self.endInsertRows()
    
    def set_sections(self, sections_data: List[Dict]) -> None:
        self.beginResetModel()
        self._sections = sections_data.copy() if sections_data else []
        self.endResetModel()
        self.dataLoaded.emit()
        logger.info(f"Set {len(self._sections)} sections and emitted dataLoaded signal")

    def get_section_id(self, row: int) -> Optional[int]:
        """
        Get the section ID for a given row.

        Args:
            row: Row index in the table

        Returns:
            Section ID or None if row is invalid
        """
        if 0 <= row < len(self._sections):
            return self._sections[row].get('id')
        logger.warning(f"Invalid row index: {row}")
        return None

    def update_section(self, section_id: int, section_data: Dict) -> bool:
        """
        Update a section in the model.

        Args:
            section_id: ID of the section to update
            section_data: Updated section data

        Returns:
            bool: True if update successful, False otherwise
        """
        for row, section in enumerate(self._sections):
            if section.get('id') == section_id:
                # Notify view before update
                self.beginResetModel()
                self._sections[row] = section_data
                self.endResetModel()

                logger.info(f"Updated section ID {section_id} at row {row}")
                return True

        logger.warning(f"Section ID {section_id} not found for update")
        return False

    def remove_section(self, section_id: int) -> bool:
        """
        Remove a section from the model.

        Args:
            section_id: ID of the section to remove

        Returns:
            bool: True if removal successful, False otherwise
        """
        for row, section in enumerate(self._sections):
            if section.get('id') == section_id:
                # Notify view of row removal
                self.beginRemoveRows(QModelIndex(), row, row)
                self._sections.pop(row)
                self.endRemoveRows()

                logger.info(f"Removed section ID {section_id} from row {row}")
                return True

        logger.warning(f"Section ID {section_id} not found for removal")
        return False

    def get_section_data(self, row: int) -> Optional[Dict]:
        """
        Get complete section data for a given row.

        Args:
            row: Row index in the table

        Returns:
            Section data dictionary or None if row is invalid
        """
        if 0 <= row < len(self._sections):
            return self._sections[row].copy()
        logger.warning(f"Invalid row index: {row}")
        return None

