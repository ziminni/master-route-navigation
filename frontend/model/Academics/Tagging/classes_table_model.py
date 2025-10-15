import logging
from typing import Dict, List, Optional

from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSignal
from PyQt6.QtGui import QColor

logger = logging.getLogger(__name__)


def parse_schedules(schedules: List[Dict]) -> str:
    """
    Parse class schedules into a formatted string representation.

    Args:
        schedules: List of schedule dictionaries, each containing:
                  - day: Day of the week (e.g., "Monday")
                  - start_time: Start time (e.g., "09:00 AM")
                  - end_time: End time (e.g., "10:30 AM")

    Returns:
        String representation of schedules with each on a new line.
        Format: "Day Start - End"
        Example: "Monday 09:00 AM - 10:30 AM\nWednesday 02:00 PM - 03:30 PM"
    """
    if not schedules or not isinstance(schedules, list):
        return ""

    formatted_schedules = []
    for schedule in schedules:
        if isinstance(schedule, dict):
            day = schedule.get('day', '')
            start_time = schedule.get('start_time', '')
            end_time = schedule.get('end_time', '')

            if day and start_time and end_time:
                formatted_schedules.append(f"{day} {start_time} - {end_time}")

    return "\n".join(formatted_schedules)

class ClassesTableModel(QAbstractTableModel):
    dataLoaded = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._classes: List[Dict] = []
        self._headers = [
            "No.",
            "Code",
            "Title",
            "Units",
            "Section",
            "Schedule",
            "Room",
            "Instructor",
            "Type",
            "Actions"]


    def rowCount(self, parent=QModelIndex()):
        return len(self._classes)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if index.row() >= len(self._classes) or index.row() < 0:
            return None

        class_obj = self._classes[index.row()]
        col = index.column()

        # Display role
        if role == Qt.ItemDataRole.DisplayRole:
            # Actions column (index 9) contains widgets, not data
            if col == 9:
                return None
            elif col == 0:  # No.
                return str(index.row() + 1)  # Auto-number rows
            elif col == 1:  # Code
                return class_obj.get('code', '')
            elif col == 2:  # Title
                return class_obj.get('title', '')
            elif col == 3:  # Units
                return str(class_obj.get('units', ''))
            elif col == 4:  # Section
                return class_obj.get('section_name', '')
            elif col == 5:  # Schedule
                return parse_schedules(class_obj.get('schedules', []))
            elif col == 6:  # Room
                return class_obj.get('room', '')
            elif col == 7:  # Instructor
                return class_obj.get('instructor', '')
            elif col == 8:  # Type
                return class_obj.get('type', '')
            return None

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            # Center-align numeric columns (No., Units)
            if col in [0, 3]:
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        elif role == Qt.ItemDataRole.BackgroundRole:
            if index.row() % 2 == 0:
                return QColor("#ffffff")
            return QColor("#f5f5f5")

        elif role == Qt.ItemDataRole.ForegroundRole:
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

    # ========================================================
    # DATA MANAGEMENT METHODS
    # ========================================================

    def add_class(self, class_data:Dict) -> None:
        logger.info("Entered add_class method")

        class_row = len(self._classes)

        self.beginInsertRows(QModelIndex(), class_row, class_row)
        self._classes.append(class_data)
        self.endInsertRows()

    def set_classes(self, classes: List[Dict]) -> None:
        self.beginResetModel()
        self._classes = classes.copy() if classes else []
        self.endResetModel()
        self.dataLoaded.emit()
        logger.info(f"Set {len(self._classes)} classes and emitted dataLoaded signal")

    def get_class_id(self, row: int) -> Optional[int]:
        """
        Get the class ID for a given row.

        Args:
            row: Row index in the table

        Returns:
            Class ID or None if row is invalid
        """
        if 0 <= row < len(self._classes):
            return self._classes[row].get('id')
        logger.warning(f"Invalid row index: {row}")
        return None

    def update_class(self, class_id: int, class_data: Dict) -> bool:
        """
        Update a class in the model.

        Args:
            class_id: ID of the class to update
            class_data: Updated class data

        Returns:
            bool: True if update successful, False otherwise
        """
        for row, class_obj in enumerate(self._classes):
            if class_obj.get('id') == class_id:
                # Notify view before update
                self.beginResetModel()
                self._classes[row] = class_data
                self.endResetModel()

                logger.info(f"Updated class ID {class_id} at row {row}")
                return True

        logger.warning(f"Class ID {class_id} not found for update")
        return False

    def remove_class(self, class_id: int) -> bool:
        """
        Remove a class from the model.

        Args:
            class_id: ID of the class to remove

        Returns:
            bool: True if removal successful, False otherwise
        """
        for row, class_obj in enumerate(self._classes):
            if class_obj.get('id') == class_id:
                # Notify view of row removal
                self.beginRemoveRows(QModelIndex(), row, row)
                self._classes.pop(row)
                self.endRemoveRows()

                logger.info(f"Removed class ID {class_id} from row {row}")
                return True

        logger.warning(f"Class ID {class_id} not found for removal")
        return False

    def get_class_data(self, row: int) -> Optional[Dict]:
        """
        Get complete class data for a given row.

        Args:
            row: Row index in the table

        Returns:
            Class data dictionary or None if row is invalid
        """
        if 0 <= row < len(self._classes):
            return self._classes[row].copy()
        logger.warning(f"Invalid row index: {row}")
        return None

