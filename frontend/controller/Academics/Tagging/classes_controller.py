import logging
from typing import Optional, Dict, List
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget

from frontend.services.Academics.Tagging.class_service import ClassService, ScheduleConflictError
from frontend.services.Academics.model.Academics.Tagging.classes_table_model import ClassesTableModel
from frontend.views.Academics.Tagging.create_class_dialog import CreateClassDialog

logger = logging.getLogger(__name__)


class ClassesController(QObject):
    """
    Controller for class operations.

    Orchestrates all CRUD operations for classes, enforcing business rules
    and coordinating between views and services.

    Attributes:
        service: ClassService instance for data operations
        model: ClassesTableModel for displaying data
        parent_widget: Parent widget for message boxes
    
    Signals:
        class_created: Emitted when a class is created (passes class data dict)
        class_updated: Emitted when a class is updated (passes class data dict)
        class_deleted: Emitted when a class is deleted (passes class_id int)
        class_archived: Emitted when a class is archived (passes class_id int)
        class_unarchived: Emitted when a class is unarchived (passes class data dict)
    """
    
    # Signals for notifying other components of changes
    class_created = pyqtSignal(dict)  # Emits created class data
    class_updated = pyqtSignal(dict)  # Emits updated class data
    class_deleted = pyqtSignal(int)   # Emits deleted class_id
    class_archived = pyqtSignal(int)  # Emits archived class_id
    class_unarchived = pyqtSignal(dict)  # Emits unarchived class data

    def __init__(self, parent_widget: Optional[QWidget] = None):
        """
        Initialize the classes controller.

        Args:
            parent_widget: Parent widget for dialogs (optional)
        """
        super().__init__(parent_widget)
        self.service = ClassService()
        self.parent = parent_widget
        self.model = None  # will be set by view

        logger.info("ClassesController initialized")

    def set_model(self, model: ClassesTableModel) -> None:
        """
        Set the table model for updating display.

        Args:
            model: ClassesTableModel instance
        """
        self.model = model
        logger.info(f"Model set for ClassesController")

    def load_classes(self) -> bool:
        """
        Load all active classes from data store.
        """
        try:
            classes = self.service.get_active_classes()
            if self.model:
                self.model.set_classes(classes)
                return True

        except Exception as e:
            logger.exception(f"Error loading classes: {e}")

        return False

    # =================================================
    # CREATE OPERATION
    # =================================================

    def handle_create_class(self, dialog: CreateClassDialog) -> tuple[bool, Optional[str]]:
        """
        Handle class creation from dialog.

        Args:
            dialog: CreateClassDialog instance

        Returns:
            tuple: (success: bool, error_message: Optional[str])
        """
        try:
            class_data = dialog.get_data()
            logger.info(f"Attempting to create class: {class_data.get('code')}")

            created_class = self.service.create(class_data)

            # Update the table model
            self.model.add_class(created_class)
            
            # Emit signal to notify other components
            self.class_created.emit(created_class)

            logger.info(f"Successfully created class ID {created_class['id']}")
            return True, None

        except ScheduleConflictError as e:
            logger.warning(f"Schedule conflict detected: {e}")
            return False, str(e)
        except Exception as e:
            logger.exception(f"Error creating class: {e}")
            error_msg = f"An unexpected error occurred: {str(e)}"
            return False, error_msg

    # =================================================
    # READ OPERATION
    # =================================================

    def get_class_by_id(self, class_id: int) -> Optional[Dict]:
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

    # =================================================
    # UPDATE OPERATION
    # =================================================

    def handle_update_class(self, class_id: int, class_data: Dict) -> tuple[bool, Optional[str]]:
        """
        Handle class update.

        Args:
            class_id: ID of class to update
            class_data: Updated class data

        Returns:
            tuple: (success: bool, error_message: Optional[str])
        """
        try:
            logger.info(f"Attempting to update class ID {class_id}")

            updated_class = self.service.update(class_id, class_data)

            # Update the table model
            self.model.update_class(class_id, updated_class)
            
            # Emit signal to notify other components
            self.class_updated.emit(updated_class)

            logger.info(f"Successfully updated class ID {class_id}")
            return True, None

        except ScheduleConflictError as e:
            logger.warning(f"Schedule conflict detected during update: {e}")
            return False, str(e)
        except Exception as e:
            logger.exception(f"Error updating class {class_id}: {e}")
            error_msg = f"An unexpected error occurred: {str(e)}"
            return False, error_msg

    # =================================================
    # DELETE OPERATION
    # =================================================

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
                
                # Emit signal to notify other components
                self.class_deleted.emit(class_id)
                
                logger.info(f"Successfully deleted class ID {class_id}")
                return True
            else:
                logger.warning(f"Class ID {class_id} not found for deletion")
                return False

        except Exception as e:
            logger.exception(f"Error deleting class {class_id}: {e}")
            return False

    # =================================================
    # ARCHIVING OPERATIONS
    # =================================================

    def handle_archive_class(self, class_id: int) -> bool:
        """
        Archive a class.

        Args:
            class_id: ID of class to archive

        Returns:
            bool: True if successful
        """
        try:
            success = self.service.archive_class(class_id)

            if success:
                # Update the table model
                self.model.remove_class(class_id)
                
                # Emit signal to notify other components (e.g., classroom home)
                self.class_archived.emit(class_id)
                
                logger.info(f"Successfully archived class ID {class_id}")
                return True
            else:
                logger.warning(f"Failed to archive class ID {class_id}")
                return False

        except Exception as e:
            logger.exception(f"Error archiving class {class_id}: {e}")
            return False

    def handle_unarchive_class(self, class_id: int) -> tuple[bool, str, int]:
        """
        Unarchive a class and its associated section if archived.

        Args:
            class_id: ID of class to unarchive

        Returns:
            tuple: (success: bool, message: str, sections_count: int)
        """
        try:
            success = self.service.unarchive_class(class_id)

            if success:
                # Get the updated class data
                class_data = self.service.get_by_id(class_id)
                if class_data:
                    # Cascade unarchive: Unarchive the section this class belongs to
                    section_id = class_data.get('section_id')
                    unarchived_count = 0
                    
                    logger.info(f"Class {class_id} has section_id: {section_id}")
                    
                    if section_id:
                        from frontend.controller.Academics.controller_manager import ControllerManager
                        manager = ControllerManager()
                        sections_controller = manager.get_sections_controller()
                        
                        # Check if the section exists and is archived
                        section_data = sections_controller.service.get_by_id(section_id)
                        if section_data:
                            is_archived = section_data.get('is_archived', False)
                            logger.info(f"Section {section_id} found, is_archived: {is_archived}")
                            
                            if is_archived:
                                if sections_controller.service.unarchive_section(section_id):
                                    # Get updated section data and emit signal
                                    updated_section_data = sections_controller.service.get_by_id(section_id)
                                    if updated_section_data:
                                        sections_controller.section_unarchived.emit(updated_section_data)
                                        logger.info(f"Section {section_id} unarchived and signal emitted")
                                    unarchived_count = 1
                                else:
                                    logger.warning(f"Failed to unarchive section {section_id}")
                            else:
                                logger.info(f"Section {section_id} is not archived, no action needed")
                        else:
                            logger.warning(f"Section {section_id} not found in database")
                    else:
                        logger.warning(f"Class {class_id} has no section_id set")
                    
                    # Emit signal to notify other components (e.g., classroom home, classes page)
                    self.class_unarchived.emit(class_data)
                    
                    logger.info(f"Successfully unarchived class ID {class_id}, {unarchived_count} section(s) also unarchived")
                    
                    if unarchived_count > 0:
                        message = f"Class unarchived successfully! Section also restored."
                    else:
                        message = "Class unarchived successfully!"
                    
                    return True, message, unarchived_count
                else:
                    logger.warning(f"Class data not found after unarchiving ID {class_id}")
                
            logger.warning(f"Failed to unarchive class ID {class_id}")
            return False, "Failed to unarchive the class.", 0

        except Exception as e:
            logger.exception(f"Error unarchiving class {class_id}: {e}")
            return False, f"An unexpected error occurred: {str(e)}", 0

    def handle_archive_all_classes(self) -> bool:
        """
        Archive all classes and emit signals for each one.

        Returns:
            bool: True if successful
        """
        try:
            # Get all active classes before archiving
            active_classes = self.service.get_active_classes()
            
            success = self.service.archive_all_classes()

            if success:
                # Emit signal for each archived class
                for class_data in active_classes:
                    self.class_archived.emit(class_data['id'])
                
                # Reload all classes to update the view
                self.load_classes()
                logger.info(f"Successfully archived all {len(active_classes)} classes")
                return True
            else:
                logger.warning("Failed to archive all classes")
                return False

        except Exception as e:
            logger.exception(f"Error archiving all classes: {e}")
            return False

