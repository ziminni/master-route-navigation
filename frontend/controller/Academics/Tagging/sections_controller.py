import logging
from typing import Optional, Dict, List
from PyQt6.QtWidgets import QWidget

from frontend.services.Academics.Tagging.section_service import SectionService
from frontend.model.Academics.Tagging.section_table_model import SectionsTableModel
from frontend.views.Academics.Tagging.create_section_dialog import CreateSectionDialog

logger = logging.getLogger(__name__)

class SectionsController:
    """
    Controller for section operations.
    
    Orchestrates all CRUD operations for sections, enforcing business rules
    and coordinating between views and services.
    
    Attributes:
        service: SectionService instance for data operations
        model: SectionsTableModel for displaying data
        parent_widget: Parent widget for message boxes
    """

    def __init__(self, parent_widget: Optional[QWidget] = None):
        """
        Initialize the sections controller.

        Args:
            parent_widget: Parent widget for dialogs (optional) 
        """
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
        Loads all sections from data store. 
        """
        try:
            sections = self.service.get_all()
            if self.model:
                self.model.set_sections(sections)
                return True

        except Exception as e:
            logger.exception(f"{e}")

        return False

    # ================================================= 
    # CREATE OPERATION
    # =================================================   

    def handle_create_section(self, dialog: CreateSectionDialog) -> bool:
        """
        Handle section creation from dialog. 

        Args:
            dialog: CreateSectionDialog instance
        
        Returns:
            bool: True if section created successfully, False otherwise
        """
        try:
            section_data = dialog.get_data() 
            logger.info(f"Attempting to create section: {section_data.get('section')}")

            if self._validate_unique_section_data(section_data):
                created_section = self.service.create(section_data)

                # update the table model
                logger.info(f"Before self.model add_section method")
                self.model.add_section(created_section) 
                logger.info(f"After self.model add_section method")

                logger.info(f"Successfully created section ID {created_section['id']}") 
                return True
        
        except Exception as e:
            logger.exception(f"An error occured while creating a section: {e}")
            return False 
        
        logger.info(f"Unable to create section. Check whether duplicate section already exists or SectionController.model has been set.")
        return False 


    def _validate_unique_section_data(self, section_data: Dict) -> bool:
        """
        Business rule validation of duplicate sections. Sections cannot have the same name, program, year, curriculum and type.

        Args:
            section_data: Section data to validate

        Returns:
            bool: True if section_data passes validation, False otherwise
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
                logger.error(f"Duplicate section data. Section {section_data['section']} already exists.")
                return False
            
        return True

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

    def handle_update_section(self, section_id: int, section_data: Dict) -> bool:
        """
        Handle section update.

        Args:
            section_id: ID of section to update
            section_data: Updated section data

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            logger.info(f"Attempting to update section ID {section_id}")

            # Validate uniqueness (excluding current section)
            if self._validate_unique_section_data_for_update(section_id, section_data):
                updated_section = self.service.update(section_id, section_data)

                # Update the table model
                self.model.update_section(section_id, updated_section)

                logger.info(f"Successfully updated section ID {section_id}")
                return True

        except Exception as e:
            logger.exception(f"Error updating section {section_id}: {e}")
            return False

        logger.warning(f"Unable to update section ID {section_id}")
        return False

    def _validate_unique_section_data_for_update(self, section_id: int, section_data: Dict) -> bool:
        """
        Validate section uniqueness during update (excluding current section).

        Args:
            section_id: ID of section being updated
            section_data: New section data

        Returns:
            bool: True if validation passes, False otherwise
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
                logger.error(f"Duplicate section data. Section {section_data['section']} already exists.")
                return False

        return True

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
