import logging
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget

from frontend.model.Academics.Tagging.classes_table_model import ClassesTableModel
from frontend.services.Academics.Tagging.class_service import ClassService
from frontend.services.Academics.Tagging.section_service import SectionService
from frontend.views.Academics.Tagging.create_class_dialog import CreateClassDialog

logger = logging.getLogger(__name__)

class ClassesController(QObject):
    class_created = pyqtSignal(dict)
    class_updated = pyqtSignal(dict)
    class_deleted = pyqtSignal(int)

    def __init__(self, parent_widget: Optional[QWidget] = None):
        super().__init__()
        self.parent = parent_widget
        self.service = ClassService()
        self.section_service = SectionService()
        self.model = None # will be set by view

        logger.info("ClassesController initialized")

    def set_model(self, model: ClassesTableModel) -> None:
        """
        Set the table model for updating display.

        Args:
            model: ClassesTableModel instance
        """

        self.model = model
        logger.info(f"Entered set_model method. model = {self.model}")

    def load_classes(self) -> bool:
        """
        Loads all classes from data store.
        """
        try:
            classes = self.service.get_all()
            if self.model:
                self.model.set_classes(classes)
                return True

        except Exception as e:
            logger.exception(f"{e}")

        return False

    # =========================================================================
    # CREATE OPERATIONS
    # =========================================================================

    def handle_create_class(self, dialog: CreateClassDialog) -> bool:
        try:
            logger.info("Entered handle_create_class method.")
            class_data = dialog.get_data()
            logger.info(f"class_data = {class_data}")
            # some kind of validation here before proceeding to next line
            created_class = self.service.create(class_data)
            self.model.add_class(created_class)

            self.class_created.emit(class_data)
            return True

        except Exception as e:
            logger.exception(f"{e}")

        return False

    # =========================================================================
    # UPDATE OPERATION
    # =========================================================================

    def get_class_by_id(self, class_id: int) -> Optional[dict]:
        """
        Get a class by its ID.

        Args:
            class_id: ID of the class to retrieve

        Returns:
            Class data dictionary or None if not found
        """
        try:
            return self.service.get_by_id(class_id)
        except Exception as e:
            logger.exception(f"Error retrieving class {class_id}: {e}")
            return None

    def handle_update_class(self, class_id: int, class_data: dict) -> bool:
        """
        Handle class update from dialog.

        Args:
            class_id: ID of class to update
            class_data: Updated class data

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            logger.info(f"Attempting to update class ID {class_id}")

            updated_class = self.service.update(class_id, class_data)

            # Update the table model
            self.model.update_class(class_id, updated_class)

            self.class_updated.emit(updated_class)
            logger.info(f"Successfully updated class ID {class_id}")
            return True

        except Exception as e:
            logger.exception(f"Error updating class {class_id}: {e}")
            return False

    # =========================================================================
    # DELETE OPERATION
    # =========================================================================

    def handle_delete_class(self, class_id: int) -> bool:
        """
        Handle class deletion.

        Args:
            class_id: ID of class to delete

        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            logger.info(f"Attempting to delete class ID {class_id}")

            success = self.service.delete(class_id)

            if success:
                # Update the table model
                self.model.remove_class(class_id)

                self.class_deleted.emit(class_id)
                logger.info(f"Successfully deleted class ID {class_id}")
                return True
            else:
                logger.warning(f"Class ID {class_id} not found for deletion")
                return False

        except Exception as e:
            logger.exception(f"Error deleting class {class_id}: {e}")
            return False


