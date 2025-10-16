#  Modified to work with unified classroom_data.json while maintaining API compatibility

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from copy import deepcopy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SectionServiceError(Exception):
    """Base exception for section service errors."""
    pass


class SectionNotFoundError(SectionServiceError):
    """Raised when a section is not found."""
    pass


class SectionValidationError(SectionServiceError):
    """Raised when section data fails validation."""
    pass


class SectionStorageError(SectionServiceError):
    """Raised when there's an error reading/writing data."""
    pass


class SectionService:
    """
    Service layer for section data operations.

    NOW USES UNIFIED classroom_data.json FILE.
    Maintains same API - controllers remain unchanged.

    Architecture Pattern:
        Controller → Service → Data Store (Unified JSON/API)
    """

    REQUIRED_FIELDS = {
        'section', 'program', 'curriculum', 'year',
        'capacity', 'type', 'remarks'
    }

    VALID_TYPES = {'Lecture', 'Laboratory', 'Hybrid'}
    VALID_YEARS = {'1st', '2nd', '3rd', '4th', '5th', 'N/A (Petition)'}

    def __init__(self, json_file: str = "services/Academics/data/classroom_data.json"):  # CHANGED: unified file
        """
        Initialize the section service.

        Args:
            json_file: Path to unified JSON database file
        """
        self.json_file = json_file
        self._cache: Optional[Dict] = None
        self._ensure_data_file_exists()

        logger.info(f"SectionService initialized with unified file: {json_file}")

    def _ensure_data_file_exists(self) -> None:
        """Ensure the unified JSON data file exists."""
        try:
            Path(self.json_file).parent.mkdir(parents=True, exist_ok=True)

            if not os.path.exists(self.json_file):
                initial_data = {
                    "users": [],
                    "sections": [],
                    "classes": [],
                    "topics": [],
                    "posts": [],
                    "enrollments": []
                }
                with open(self.json_file, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, indent=4, ensure_ascii=False)
                logger.info(f"Created unified classroom database: {self.json_file}")

        except Exception as e:
            error_msg = f"Failed to initialize data file: {str(e)}"
            logger.error(error_msg)
            raise SectionStorageError(error_msg)

    def _load_data(self) -> Dict:
        """Load data from unified JSON file."""
        # if self._cache is not None:
        #     return deepcopy(self._cache)

        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"{data} loaded from {self.json_file}")

            # Ensure required keys exist
            if 'sections' not in data:
                data['sections'] = []
            if 'classes' not in data:
                data['classes'] = []
            if 'topics' not in data:
                data['topics'] = []
            if 'posts' not in data:
                data['posts'] = []
            if 'users' not in data:
                data['users'] = []
            if 'enrollments' not in data:
                data['enrollments'] = []

            self._cache = deepcopy(data)
            logger.debug(f"Loaded {len(data['sections'])} sections from unified file")
            return deepcopy(data)

        except FileNotFoundError:
            error_msg = f"Data file not found: {self.json_file}"
            logger.error(error_msg)
            raise SectionStorageError(error_msg)

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in data file: {str(e)}"
            logger.error(error_msg)
            raise SectionStorageError(error_msg)

        except Exception as e:
            error_msg = f"Error loading data: {str(e)}"
            logger.error(error_msg)
            raise SectionStorageError(error_msg)

    def _save_data(self, data: Dict) -> None:
        """Save data to unified JSON file atomically."""
        temp_file = f"{self.json_file}.tmp"

        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            os.replace(temp_file, self.json_file)
            self._cache = None

            logger.debug(f"Saved {len(data['sections'])} sections to unified file")

        except Exception as e:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

            error_msg = f"Error saving data: {str(e)}"
            logger.error(error_msg)
            raise SectionStorageError(error_msg)

    def _generate_next_id(self, data: Dict) -> int:
        """
        Generate the next available ID for a new section.
        Uses max existing ID + 1 approach (no metadata).
        """
        if not data['sections']:
            return 1

        existing_ids = {sec['id'] for sec in data['sections'] if 'id' in sec}
        if not existing_ids:
            return 1

        return max(existing_ids) + 1

    def _validate_section_data(self, data: Dict, is_update: bool = False) -> None:
        """Validate section data at storage level."""
        if not is_update:
            missing_fields = self.REQUIRED_FIELDS - set(data.keys())
            if missing_fields:
                raise SectionValidationError(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )

        if 'capacity' in data:
            try:
                capacity = int(data['capacity'])
                if capacity <= 0:
                    raise SectionValidationError("Capacity must be a positive integer")
            except (ValueError, TypeError):
                raise SectionValidationError("Capacity must be a valid integer")

        if 'type' in data and data['type'] not in self.VALID_TYPES:
            raise SectionValidationError(
                f"Invalid type. Must be one of: {', '.join(self.VALID_TYPES)}"
            )

        if 'year' in data and data['year'] not in self.VALID_YEARS:
            raise SectionValidationError(
                f"Invalid year. Must be one of: {', '.join(self.VALID_YEARS)}"
            )

        string_fields = ['section', 'program', 'curriculum']
        for field in string_fields:
            if field in data:
                if not isinstance(data[field], str) or not data[field].strip():
                    raise SectionValidationError(
                        f"{field.capitalize()} must be a non-empty string"
                    )

    # ========================================================================
    # PUBLIC CRUD METHODS - API UNCHANGED
    # ========================================================================

    def get_all(self, token: str = None) -> List[Dict]:
        """Retrieve all sections. API unchanged."""
        try:
            data = self._load_data()
            logger.info(f"Retrieved {len(data['sections'])} sections")
            return deepcopy(data['sections'])
        except Exception as e:
            logger.error(f"Error retrieving sections: {str(e)}")
            raise

    def get_by_id(self, section_id: int, token: str = None) -> Optional[Dict]:
        """Retrieve a specific section by ID. API unchanged."""
        try:
            data = self._load_data()
            for section in data['sections']:
                if section.get('id') == section_id:
                    logger.debug(f"Found section with ID {section_id}")
                    return deepcopy(section)

            logger.warning(f"Section with ID {section_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving section {section_id}: {str(e)}")
            raise

    def create(self, section_data: Dict, token: str = None) -> Dict:
        """Create a new section. API unchanged."""
        try:
            self._validate_section_data(section_data, is_update=False)

            data = self._load_data()

            new_section = deepcopy(section_data)
            new_section['id'] = self._generate_next_id(data)
            new_section['created_at'] = datetime.now().isoformat()
            new_section['updated_at'] = datetime.now().isoformat()

            data['sections'].append(new_section)
            self._save_data(data)

            logger.info(f"Created section: {new_section['section']} (ID: {new_section['id']})")
            return deepcopy(new_section)

        except (SectionValidationError, SectionStorageError):
            raise
        except Exception as e:
            error_msg = f"Unexpected error creating section: {str(e)}"
            logger.error(error_msg)
            raise SectionStorageError(error_msg)

    def update(self, section_id: int, section_data: Dict, token: str = None) -> Dict:
        """Update an existing section. API unchanged."""
        try:
            self._validate_section_data(section_data, is_update=True)

            data = self._load_data()

            section_index = None
            for i, section in enumerate(data['sections']):
                if section.get('id') == section_id:
                    section_index = i
                    break

            if section_index is None:
                raise SectionNotFoundError(f"Section with ID {section_id} not found")

            existing_section = data['sections'][section_index]
            existing_section.update(section_data)
            existing_section['updated_at'] = datetime.now().isoformat()
            existing_section['id'] = section_id

            if 'created_at' not in existing_section:
                existing_section['created_at'] = datetime.now().isoformat()

            self._save_data(data)

            logger.info(f"Updated section ID {section_id}")
            return deepcopy(existing_section)

        except (SectionNotFoundError, SectionValidationError, SectionStorageError):
            raise
        except Exception as e:
            error_msg = f"Unexpected error updating section: {str(e)}"
            logger.error(error_msg)
            raise SectionStorageError(error_msg)

    def delete(self, section_id: int, token: str = None) -> bool:
        """Delete a section. API unchanged."""
        try:
            data = self._load_data()

            original_count = len(data['sections'])
            data['sections'] = [
                s for s in data['sections'] if s.get('id') != section_id
            ]

            if len(data['sections']) == original_count:
                logger.warning(f"Section with ID {section_id} not found")
                return False

            self._save_data(data)
            logger.info(f"Deleted section ID {section_id}")
            return True

        except Exception as e:
            error_msg = f"Error deleting section {section_id}: {str(e)}"
            logger.error(error_msg)
            raise SectionStorageError(error_msg)

    def search(self, filters: Dict, token: str = None) -> List[Dict]:
        """Search sections by criteria. API unchanged."""
        try:
            all_sections = self.get_all(token)

            if not filters:
                return all_sections

            results = []
            for section in all_sections:
                match = True
                for key, value in filters.items():
                    if key not in section or section[key] != value:
                        match = False
                        break
                if match:
                    results.append(section)

            logger.info(f"Search found {len(results)} sections")
            return results
        except Exception as e:
            logger.error(f"Error searching sections: {str(e)}")
            raise