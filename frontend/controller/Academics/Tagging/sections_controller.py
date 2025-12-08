import logging
from typing import Optional, Dict, List
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget

from frontend.services.Academics.Tagging.section_service import SectionService
from frontend.services.Academics.model.Academics.Tagging.section_table_model import SectionsTableModel
from frontend.views.Academics.Tagging.create_section_dialog import CreateSectionDialog

logger = logging.getLogger(__name__)

class SectionsController(QObject):
    """
    Controller for section operations.
    
    Orchestrates all CRUD operations for sections, enforcing business rules
    and coordinating between views and services.
    
    Attributes:
        service: SectionService instance for data operations
        model: SectionsTableModel for displaying data
        parent_widget: Parent widget for message boxes
    
    Signals:
        section_created: Emitted when a section is created (passes section data dict)
        section_updated: Emitted when a section is updated (passes section data dict)
        section_deleted: Emitted when a section is deleted (passes section_id int)
        section_archived: Emitted when a section is archived (passes section_id int)
        section_unarchived: Emitted when a section is unarchived (passes section data dict)
    """
    
    # Signals for notifying other components of changes
    section_created = pyqtSignal(dict)  # Emits created section data
    section_updated = pyqtSignal(dict)  # Emits updated section data
    section_deleted = pyqtSignal(int)   # Emits deleted section_id
    section_archived = pyqtSignal(int)  # Emits archived section_id
    section_unarchived = pyqtSignal(dict)  # Emits unarchived section data

    def __init__(self, parent_widget: Optional[QWidget] = None):
        """
        Initialize the sections controller.

        Args:
            parent_widget: Parent widget for dialogs (optional) 
        """
        super().__init__(parent_widget)
        self.service = SectionService()
        self.parent = parent_widget 
        self.model = None # will be set by view 

        logger.info("SectionsController initialized")

    def set_model(self, model: SectionsTableModel) -> None:
        """
        Set the table model for updating display.
        
        Args:
            model: SectionsTableModel instance
        """
        
        self.model = model 
        logger.info(f"Entered set_model method. model = {self.model}")

    def load_sections(self) -> bool:
        """
        Loads all active (non-archived) sections from data store.
        """
        try:
            sections = self.service.get_active_sections()
            if self.model:
                self.model.set_sections(sections)
                return True

        except Exception as e:
            logger.exception(f"{e}")

        return False

    # ================================================= 
    # CREATE OPERATION
    # =================================================   

    def handle_create_section(self, dialog: CreateSectionDialog) -> tuple[bool, Optional[str]]:
        """
        Handle section creation from dialog. 

        Args:
            dialog: CreateSectionDialog instance
        
        Returns:
             tuple: (success: bool, error_message: Optional[str])
        """
        try:
            section_data = dialog.get_data()
            logger.info(f"Attempting to create section: {section_data.get('section')}")

            # Check for duplicates
            validation_result, error_message = self._validate_unique_section_data(section_data)

            if validation_result:
                created_section = self.service.create(section_data)

                # update the table model
                logger.info(f"Before self.model add_section method")
                self.model.add_section(created_section)
                logger.info(f"After self.model add_section method")

                logger.info(f"Successfully created section ID {created_section['id']}")
                return True, None
            else:
                # Validation failed - duplicate found
                logger.warning(f"Duplicate section detected: {error_message}")
                return False, error_message

        except Exception as e:
            logger.exception(f"An error occured while creating a section: {e}")
            error_msg = f"An unexpected error occurred: {str(e)}"
            return False, error_msg

        logger.info(f"Unable to create section. Check whether duplicate section already exists or SectionController.model has been set.")
        return False, "Unable to create section. Please check your input."


    def _validate_unique_section_data(self, section_data: Dict) -> tuple[bool, Optional[str]]:
        """
        Business rule validation of duplicate sections. Sections cannot have the same name, program, year, curriculum and type.

        Args:
            section_data: Section data to validate

        Returns:
            tuple: (is_valid: bool, error_message: Optional[str])
        """
        existing_sections = self.service.get_all() 

        for existing in existing_sections:
            if (
                existing['section'] == section_data['section'] and
                existing['program'] == section_data['program'] and 
                existing['year'] == section_data['year'] and 
                existing['curriculum'] == section_data['curriculum'] and
                existing['type'] == section_data['type']
            ):
                error_message = (
                    f"Duplicate section detected!\n\n"
                    f"Section: {section_data['section']}\n"
                    f"Program: {section_data['program']}\n"
                    f"Year: {section_data['year']}\n"
                    f"Curriculum: {section_data['curriculum']}\n"
                    f"Type: {section_data['type']}\n\n"
                    f"A section with these exact details already exists."
                )
                logger.error(f"Duplicate section data. Section {section_data['section']} already exists.")
                return False, error_message
            
        return True, None

        # =================================================

    # UPDATE OPERATION
    # =================================================

    def get_section_by_id(self, section_id: int) -> Optional[Dict]:
        """
        Get a section by its ID.

        Args:
            section_id: ID of the section to retrieve

        Returns:
            Section data dictionary or None if not found
        """
        try:
            return self.service.get_by_id(section_id)
        except Exception as e:
            logger.exception(f"Error retrieving section {section_id}: {e}")
            return None

    def can_edit_section(self, section_id: int) -> tuple[bool, Optional[str]]:
        """
        Check if a section can be edited (doesn't have associated classes).

        Args:
            section_id: ID of section to check

        Returns:
            tuple: (can_edit: bool, error_message: Optional[str])
        """
        if self._section_has_classes(section_id):
            error_message = (
                "This section cannot be edited because it has associated classes.\n\n"
                "To edit this section, you must first delete or reassign all classes "
                "associated with it."
            )
            return False, error_message

        return True, None

    def handle_update_section(self, section_id: int, section_data: Dict) -> tuple[bool, Optional[str]]:
        """
        Handle section update.

        Args:
            section_id: ID of section to update
            section_data: Updated section data

        Returns:
            tuple: (success: bool, error_message: Optional[str])
        """
        try:
            logger.info(f"Attempting to update section ID {section_id}")

            can_edit, error_message = self.can_edit_section(section_id)
            if not can_edit:
                logger.warning(f"Cannot edit section {section_id}: has associated classes")
                return False, error_message

            # Validate uniqueness (excluding current section)
            validation_result, error_message = self._validate_unique_section_data_for_update(section_id, section_data)

            if validation_result:
                updated_section = self.service.update(section_id, section_data)

                # Update the table model
                self.model.update_section(section_id, updated_section)

                logger.info(f"Successfully updated section ID {section_id}")
                return True, None
            else:
                logger.warning(f"Duplicate section detected during update: {error_message}")
                return False, error_message

        except Exception as e:
            logger.exception(f"Error updating section {section_id}: {e}")
            error_msg = f"An unexpected error occurred: {str(e)}"
            return False, error_msg

        logger.warning(f"Unable to update section ID {section_id}")
        return False, "Unable to update section. Please check your input."

    def _validate_unique_section_data_for_update(self, section_id: int, section_data: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate section uniqueness during update (excluding current section).

        Args:
            section_id: ID of section being updated
            section_data: New section data

        Returns:
             tuple: (is_valid: bool, error_message: Optional[str])
        """
        existing_sections = self.service.get_all()

        for existing in existing_sections:
            # Skip the section being updated
            if existing['id'] == section_id:
                continue

            if (
                    existing['section'] == section_data['section'] and
                    existing['program'] == section_data['program'] and
                    existing['year'] == section_data['year'] and
                    existing['curriculum'] == section_data['curriculum'] and
                    existing['type'] == section_data['type']
            ):
                error_message = (
                    f"Duplicate section detected!\n\n"
                    f"Section: {section_data['section']}\n"
                    f"Program: {section_data['program']}\n"
                    f"Year: {section_data['year']}\n"
                    f"Curriculum: {section_data['curriculum']}\n"
                    f"Type: {section_data['type']}\n\n"
                    f"A section with these exact details already exists."
                )
                logger.error(f"Duplicate section data. Section {section_data['section']} already exists.")
                return False, error_message

        return True, None

    # =================================================
    # DELETE OPERATION
    # =================================================

    def handle_delete_section(self, section_id: int) -> bool:
        """
        Handle section deletion.

        Args:
            section_id: ID of section to delete

        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            logger.info(f"Attempting to delete section ID {section_id}")

            # Check if section has associated classes
            if self._section_has_classes(section_id):
                logger.warning(f"Cannot delete section {section_id}: has associated classes")
                return False

            success = self.service.delete(section_id)

            if success:
                # Update the table model
                self.model.remove_section(section_id)
                logger.info(f"Successfully deleted section ID {section_id}")
                return True
            else:
                logger.warning(f"Section ID {section_id} not found for deletion")
                return False

        except Exception as e:
            logger.exception(f"Error deleting section {section_id}: {e}")
            return False

    def _section_has_classes(self, section_id: int) -> bool:
        """
        Check if a section has associated classes.

        Args:
            section_id: ID of section to check

        Returns:
            bool: True if section has classes, False otherwise
        """
        try:
            from frontend.services.Academics.Tagging.class_service import ClassService
            class_service = ClassService()
            classes = class_service.get_by_section(section_id)
            return len(classes) > 0
        except Exception as e:
            logger.error(f"Error checking classes for section {section_id}: {e}")
            return False

    # =================================================
    # ARCHIVING OPERATIONS
    # =================================================

    def handle_archive_section(self, section_id: int) -> tuple[bool, Optional[str]]:
        """
        Archive a section. Can only archive if all classes are already archived.

        Args:
            section_id: ID of section to archive

        Returns:
            tuple: (success: bool, error_message: Optional[str])
        """
        try:
            from frontend.services.Academics.Tagging.class_service import ClassService
            class_service = ClassService()

            # Check if section has any active classes
            if class_service.has_active_classes_for_section(section_id):
                error_message = (
                    "Cannot archive section. Some associated Classes are still active.\n\n"
                    "Please archive all Classes first."
                )
                logger.warning(f"Cannot archive section {section_id}: has active classes")
                return False, error_message

            success = self.service.archive_section(section_id)

            if success:
                # Emit signal to notify all listening components (SectionsPage, ArchivedSectionsPage)
                # Each page will handle the refresh appropriately
                self.section_archived.emit(section_id)
                
                logger.info(f"Successfully archived section ID {section_id}, signal emitted")
                return True, None
            else:
                logger.warning(f"Failed to archive section ID {section_id}")
                return False, "Failed to archive section."

        except Exception as e:
            logger.exception(f"Error archiving section {section_id}: {e}")
            error_msg = f"An unexpected error occurred: {str(e)}"
            return False, error_msg

    def handle_unarchive_section(self, section_id: int) -> bool:
        """
        Unarchive a section.

        Args:
            section_id: ID of section to unarchive

        Returns:
            bool: True if successful
        """
        try:
            success = self.service.unarchive_section(section_id)

            if success:
                # Emit signal to notify all listening components (SectionsPage, ArchivedSectionsPage)
                # Each page will handle the refresh appropriately
                section_data = self.service.get_by_id(section_id)
                if section_data:
                    self.section_unarchived.emit(section_data)
                    logger.info(f"Successfully unarchived section ID {section_id}, signal emitted")
                else:
                    logger.warning(f"Section data not found after unarchiving ID {section_id}")
                
                return True
            else:
                logger.warning(f"Failed to unarchive section ID {section_id}")
                return False

        except Exception as e:
            logger.exception(f"Error unarchiving section {section_id}: {e}")
            return False

    def handle_archive_all_sections(self) -> tuple[bool, Optional[str]]:
        """
        Archive all sections. Can only archive if all classes are already archived.

        Returns:
            tuple: (success: bool, error_message: Optional[str])
        """
        try:
            from frontend.services.Academics.Tagging.class_service import ClassService
            class_service = ClassService()

            # Check if any section has active classes
            all_sections = self.service.get_all()
            sections_with_active_classes = []

            for section in all_sections:
                if not section.get('is_archived', False):
                    if class_service.has_active_classes_for_section(section['id']):
                        sections_with_active_classes.append(section['section'])

            if sections_with_active_classes:
                error_message = (
                    "Cannot archive Section(s). Some associated Classes are still active.\n\n"
                    f"Sections with active classes: {', '.join(sections_with_active_classes)}\n\n"
                    "Please archive all Classes first."
                )
                logger.warning("Cannot archive all sections: some have active classes")
                return False, error_message

            # Get all active sections before archiving
            active_sections = [s for s in all_sections if not s.get('is_archived', False)]
            
            success, failed_ids = self.service.archive_all_sections()

            if success:
                # Emit signal for each archived section
                for section_data in active_sections:
                    self.section_archived.emit(section_data['id'])
                
                # Reload all sections to update the view
                self.load_sections()
                logger.info(f"Successfully archived all {len(active_sections)} sections")
                return True, None
            else:
                error_message = f"Failed to archive some sections: {failed_ids}"
                logger.warning(error_message)
                return False, error_message

        except Exception as e:
            logger.exception(f"Error archiving all sections: {e}")
            error_msg = f"An unexpected error occurred: {str(e)}"
            return False, error_msg

