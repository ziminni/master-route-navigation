#  Modified to work with unified classroom_data.json while maintaining API compatibility

import json
import logging
import os
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from copy import deepcopy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_section_name(section: Dict) -> str:
    """
    Generate formatted section name from section data.

    Args:
        section: Section dictionary containing:
                - program: Full program name (e.g., "BS Computer Science")
                - year: Year level (e.g., "3rd")
                - section: Section letter (e.g., "C")

    Returns:
        Formatted section name (e.g., "BSCS-3C")

    Example:
        >>> section = {"program": "BS Computer Science", "year": "3rd", "section": "C"}
        >>> generate_section_name(section)
        'BSCS-3C'
    """
    if not section:
        return "Unknown"

    # Extract program acronym from full program name
    program = section.get('program', '')
    year = section.get('year', '')
    section_letter = section.get('section', '')

    # Generate program acronym (e.g., "BS Computer Science" -> "BSCS")
    program_acronym = ''
    if program:
        # Take all capital letters and first letters of words
        words = program.split()
        for word in words:
            # If word is all caps (like "BS", "IT"), take the whole thing
            if word.isupper():
                program_acronym += word
            else:
                # Otherwise take first letter if it's uppercase
                if word and word[0].isupper():
                    program_acronym += word[0]

    # Extract year number (e.g., "3rd" -> "3")
    year_num = ''
    if year:
        year_num = ''.join(filter(str.isdigit, year))

    # Combine: PROGRAM-YEARSECTION (e.g., "BSCS-3C")
    if program_acronym and year_num and section_letter:
        return f"{program_acronym}-{year_num}{section_letter}"
    elif section_letter:
        return section_letter
    else:
        return "Unknown"


class ClassServiceError(Exception):
    """Base exception for class service errors."""
    pass


class ClassNotFoundError(ClassServiceError):
    """Raised when a class is not found."""
    pass


class ClassValidationError(ClassServiceError):
    """Raised when class data fails validation."""
    pass


class ClassStorageError(ClassServiceError):
    """Raised when there's an error reading/writing data."""
    pass


class ScheduleConflictError(ClassServiceError):
    """Raised when schedule conflicts are detected."""
    pass


class ClassService:
    """
    Service layer for class data operations.

    NOW USES UNIFIED classroom_data.json FILE.
    Maintains same API - controllers remain unchanged.

    Architecture Pattern:
        Controller → Service → Data Store (Unified JSON/API)

    Attributes:
        json_file (str): Path to the unified classroom_data.json file
        section_service: Reference to SectionService for validation
        _cache (Dict): In-memory cache of loaded data
    """

    # Required fields for a valid class
    REQUIRED_FIELDS = {
        'code', 'title', 'units', 'section_id',
        'schedules', 'room', 'instructor', 'type'
    }

    # Schedule required fields
    SCHEDULE_REQUIRED_FIELDS = {'day', 'start_time', 'end_time'}

    # Valid values
    VALID_DAYS = {
        'Monday', 'Tuesday', 'Wednesday', 'Thursday',
        'Friday', 'Saturday', 'Sunday'
    }
    VALID_CLASS_TYPES = {'Lecture', 'Laboratory'}

    def __init__(
            self,
            json_file: str = "services/Academics/data/classroom_data.json",  # CHANGED: unified file
            section_service=None
    ):
        """
        Initialize the class service.

        Args:
            json_file: Path to unified JSON database file
            section_service: SectionService instance for validation
        """
        self.json_file = json_file
        self._cache: Optional[Dict] = None

        # Import here to avoid circular dependency
        if section_service is None:
            from frontend.services.Academics.Tagging.section_service import SectionService
            self.section_service = SectionService()
        else:
            self.section_service = section_service

        self._ensure_data_file_exists()

        logger.info(f"ClassService initialized with unified file: {json_file}")

    def _ensure_data_file_exists(self) -> None:
        """
        Ensure the unified JSON data file exists.
        Creates unified structure with all entities.
        """
        try:
            Path(self.json_file).parent.mkdir(parents=True, exist_ok=True)

            if not os.path.exists(self.json_file):
                # Create unified structure
                initial_data = {
                    "users": [],
                    "sections": [],  # Added for unified structure
                    "classes": [],
                    "topics": [],
                    "posts": [],
                    "enrollments": []  # Added for future use
                }
                with open(self.json_file, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, indent=4, ensure_ascii=False)
                logger.info(f"Created unified classroom database: {self.json_file}")

        except Exception as e:
            error_msg = f"Failed to initialize data file: {str(e)}"
            logger.error(error_msg)
            raise ClassStorageError(error_msg)

    def _load_data(self) -> Dict:
        """
        Load data from unified JSON file.

        Returns:
            Dict: Complete unified JSON structure
        """
        if self._cache is not None:
            return deepcopy(self._cache)

        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Ensure required keys exist
            if 'classes' not in data:
                data['classes'] = []
            if 'sections' not in data:
                data['sections'] = []
            if 'topics' not in data:
                data['topics'] = []
            if 'posts' not in data:
                data['posts'] = []
            if 'users' not in data:
                data['users'] = []
            if 'enrollments' not in data:
                data['enrollments'] = []

            self._cache = deepcopy(data)
            logger.debug(f"Loaded {len(data['classes'])} classes from unified file")
            return deepcopy(data)

        except FileNotFoundError:
            error_msg = f"Data file not found: {self.json_file}"
            logger.error(error_msg)
            raise ClassStorageError(error_msg)

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in data file: {str(e)}"
            logger.error(error_msg)
            raise ClassStorageError(error_msg)

        except Exception as e:
            error_msg = f"Error loading data: {str(e)}"
            logger.error(error_msg)
            raise ClassStorageError(error_msg)

    def _save_data(self, data: Dict) -> None:
        """
        Save data to unified JSON file atomically.

        Args:
            data: Complete unified JSON structure to save
        """
        temp_file = f"{self.json_file}.tmp"

        try:
            # No metadata in unified structure - data is saved as-is

            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            os.replace(temp_file, self.json_file)
            self._cache = None

            logger.debug(f"Saved {len(data['classes'])} classes to unified file")

        except Exception as e:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

            error_msg = f"Error saving data: {str(e)}"
            logger.error(error_msg)
            raise ClassStorageError(error_msg)

    def _generate_next_id(self, data: Dict) -> int:
        """
        Generate the next available ID for a new class.
        Uses max existing ID + 1 approach (no metadata).

        Args:
            data: Current unified data structure

        Returns:
            int: Next available ID
        """
        if not data['classes']:
            return 1

        existing_ids = {cls['id'] for cls in data['classes'] if 'id' in cls}
        if not existing_ids:
            return 1

        return max(existing_ids) + 1

    # ... (all validation methods remain the same) ...

    def _validate_schedule(self, schedule: Dict) -> None:
        """Validate a single schedule entry."""
        missing = self.SCHEDULE_REQUIRED_FIELDS - set(schedule.keys())
        if missing:
            raise ClassValidationError(
                f"Schedule missing fields: {', '.join(missing)}"
            )

        if schedule['day'] not in self.VALID_DAYS:
            raise ClassValidationError(
                f"Invalid day '{schedule['day']}'. "
                f"Must be one of: {', '.join(self.VALID_DAYS)}"
            )

        try:
            start = self._parse_time(schedule['start_time'])
            end = self._parse_time(schedule['end_time'])

            if end <= start:
                raise ClassValidationError(
                    f"End time ({schedule['end_time']}) must be after "
                    f"start time ({schedule['start_time']})"
                )
        except ValueError as e:
            raise ClassValidationError(f"Invalid time format: {str(e)}")

    def _parse_time(self, time_str: str) -> time:
        """Parse time string in format 'HH:MM AM/PM'."""
        try:
            time_str = time_str.strip().upper()
            if time_str[-2:] in ['AM', 'PM'] and time_str[-3] != ' ':
                time_str = time_str[:-2] + ' ' + time_str[-2:]
            return datetime.strptime(time_str, "%I:%M %p").time()
        except:
            raise ValueError(
                f"Time '{time_str}' must be in format 'HH:MM AM' or 'HH:MM PM'"
            )

    def _validate_class_data(self, data: Dict, is_update: bool = False) -> None:
        """Validate class data at storage level."""
        if not is_update:
            missing_fields = self.REQUIRED_FIELDS - set(data.keys())
            if missing_fields:
                raise ClassValidationError(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )

        if 'units' in data:
            try:
                units = int(data['units'])
                if units < 1 or units > 6:
                    raise ClassValidationError("Units must be between 1 and 6")
            except (ValueError, TypeError):
                raise ClassValidationError("Units must be a valid integer")

        if 'section_id' in data:
            try:
                section = self.section_service.get_by_id(data['section_id'])
                if section is None:
                    raise ClassValidationError(
                        f"Section with ID {data['section_id']} does not exist"
                    )
            except Exception as e:
                raise ClassValidationError(f"Error validating section_id: {str(e)}")

        if 'schedules' in data:
            if not isinstance(data['schedules'], list):
                raise ClassValidationError("Schedules must be a list")
            if len(data['schedules']) == 0:
                raise ClassValidationError("Class must have at least one schedule")
            for i, schedule in enumerate(data['schedules']):
                try:
                    self._validate_schedule(schedule)
                except ClassValidationError as e:
                    raise ClassValidationError(f"Schedule {i + 1} invalid: {str(e)}")

        if 'type' in data and data['type'] not in self.VALID_CLASS_TYPES:
            raise ClassValidationError(
                f"Invalid type. Must be one of: {', '.join(self.VALID_CLASS_TYPES)}"
            )

        string_fields = ['code', 'title', 'instructor', 'room']
        for field in string_fields:
            if field in data:
                if not isinstance(data[field], str) or not data[field].strip():
                    raise ClassValidationError(
                        f"{field.capitalize()} must be a non-empty string"
                    )

    def _check_schedule_conflicts(
            self,
            schedules: List[Dict],
            room: str,
            exclude_class_id: int = None
    ) -> List[str]:
        """Check for schedule conflicts with other classes."""
        conflicts = []

        try:
            all_classes = self.get_all()

            for existing_class in all_classes:
                if exclude_class_id and existing_class['id'] == exclude_class_id:
                    continue

                if existing_class['room'] != room:
                    continue

                for new_schedule in schedules:
                    for existing_schedule in existing_class['schedules']:
                        if new_schedule['day'] != existing_schedule['day']:
                            continue

                        new_start = self._parse_time(new_schedule['start_time'])
                        new_end = self._parse_time(new_schedule['end_time'])
                        exist_start = self._parse_time(existing_schedule['start_time'])
                        exist_end = self._parse_time(existing_schedule['end_time'])

                        if new_start < exist_end and new_end > exist_start:
                            conflict_msg = (
                                f"Conflict with {existing_class['code']} "
                                f"({existing_class['title']}) in {room} "
                                f"on {new_schedule['day']} "
                                f"{existing_schedule['start_time']} - "
                                f"{existing_schedule['end_time']}"
                            )
                            conflicts.append(conflict_msg)

        except Exception as e:
            logger.error(f"Error checking conflicts: {str(e)}")

        return conflicts

    def _check_faculty_schedule_conflicts(
            self,
            schedules: List[Dict],
            instructor: str,
            exclude_class_id: int = None
    ) -> List[str]:
        """
        Check for faculty schedule conflicts.

        A faculty member cannot teach multiple classes at the same time.

        Args:
            schedules: List of schedule dictionaries for the class
            instructor: Name of the instructor
            exclude_class_id: Class ID to exclude from conflict check (for updates)

        Returns:
            List of conflict messages
        """
        conflicts = []

        try:
            all_classes = self.get_all()

            for existing_class in all_classes:
                # Skip the class being updated
                if exclude_class_id and existing_class['id'] == exclude_class_id:
                    continue

                # Only check classes taught by the same instructor
                if existing_class.get('instructor', '').strip().lower() != instructor.strip().lower():
                    continue

                # Check for time conflicts
                for new_schedule in schedules:
                    for existing_schedule in existing_class.get('schedules', []):
                        # Must be the same day
                        if new_schedule['day'] != existing_schedule['day']:
                            continue

                        # Parse times
                        try:
                            new_start = self._parse_time(new_schedule['start_time'])
                            new_end = self._parse_time(new_schedule['end_time'])
                            exist_start = self._parse_time(existing_schedule['start_time'])
                            exist_end = self._parse_time(existing_schedule['end_time'])
                        except Exception as e:
                            logger.warning(f"Error parsing time during faculty conflict check: {e}")
                            continue

                        # Check for overlap: (start1 < end2) AND (end1 > start2)
                        if new_start < exist_end and new_end > exist_start:
                            section_name = existing_class.get('section_name', 'Unknown')
                            conflict_msg = (
                                f"Faculty conflict: {instructor} is already teaching "
                                f"{existing_class['code']} ({existing_class['title']}) "
                                f"for section {section_name} "
                                f"on {new_schedule['day']} "
                                f"{existing_schedule['start_time']} - {existing_schedule['end_time']}"
                            )
                            conflicts.append(conflict_msg)

        except Exception as e:
            logger.error(f"Error checking faculty conflicts: {str(e)}")

        return conflicts

    # ========================================================================
    # PUBLIC CRUD METHODS - API UNCHANGED
    # ========================================================================

    def get_all(self, token: str = None) -> List[Dict]:
        """Retrieve all classes. API unchanged."""
        try:
            data = self._load_data()
            logger.info(f"Retrieved {len(data['classes'])} classes")
            return deepcopy(data['classes'])
        except Exception as e:
            logger.error(f"Error retrieving classes: {str(e)}")
            raise

    def get_by_id(self, class_id: int, token: str = None) -> Optional[Dict]:
        """Retrieve a specific class by ID. API unchanged."""
        try:
            data = self._load_data()
            for cls in data['classes']:
                if cls.get('id') == class_id:
                    logger.debug(f"Found class with ID {class_id}")
                    return deepcopy(cls)

            logger.warning(f"Class with ID {class_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving class {class_id}: {str(e)}")
            raise

    def get_by_section(self, section_id: int, token: str = None) -> List[Dict]:
        """Retrieve all classes for a specific section. API unchanged."""
        try:
            all_classes = self.get_all(token)
            section_classes = [
                cls for cls in all_classes
                if cls.get('section_id') == section_id
            ]
            logger.info(f"Found {len(section_classes)} classes for section {section_id}")
            return section_classes
        except Exception as e:
            logger.error(f"Error retrieving classes for section: {str(e)}")
            raise

    def create(
            self,
            class_data: Dict,
            token: str = None,
            check_conflicts: bool = True
    ) -> Dict:
        """Create a new class. API unchanged."""
        try:
            self._validate_class_data(class_data, is_update=False)

            if check_conflicts:
                room_conflicts = self._check_schedule_conflicts(
                    class_data['schedules'],
                    class_data['room']
                )

                # Check faculty conflicts
                faculty_conflicts = self._check_faculty_schedule_conflicts(
                    class_data['schedules'],
                    class_data['instructor']
                )

                # Combine all conflicts
                all_conflicts = room_conflicts + faculty_conflicts

                if all_conflicts:
                    raise ScheduleConflictError(
                        "Schedule conflicts detected:\n" + "\n".join(all_conflicts)
                    )

            section = self.section_service.get_by_id(class_data['section_id'])
            section_name = generate_section_name(section) if section else 'Unknown'

            data = self._load_data()

            new_class = deepcopy(class_data)
            new_class['id'] = self._generate_next_id(data)
            new_class['section_name'] = section_name
            new_class['created_at'] = datetime.now().isoformat()
            new_class['updated_at'] = datetime.now().isoformat()

            # Add instructor_id if not present (for classroom compatibility)
            if 'instructor_id' not in new_class:
                new_class['instructor_id'] = f"faculty_{new_class['id']}"

            data['classes'].append(new_class)
            self._save_data(data)

            logger.info(f"Created class: {new_class['code']} (ID: {new_class['id']})")
            return deepcopy(new_class)

        except (ClassValidationError, ScheduleConflictError, ClassStorageError):
            raise
        except Exception as e:
            error_msg = f"Unexpected error creating class: {str(e)}"
            logger.error(error_msg)
            raise ClassStorageError(error_msg)

    def update(
            self,
            class_id: int,
            class_data: Dict,
            token: str = None,
            check_conflicts: bool = True
    ) -> Dict:
        """Update an existing class. API unchanged."""
        try:
            self._validate_class_data(class_data, is_update=True)

            data = self._load_data()

            class_index = None
            for i, cls in enumerate(data['classes']):
                if cls.get('id') == class_id:
                    class_index = i
                    break

            if class_index is None:
                raise ClassNotFoundError(f"Class with ID {class_id} not found")

            existing_class = data['classes'][class_index]

            if check_conflicts:
                schedules_to_check = class_data.get('schedules', existing_class['schedules'])
                room_to_check = class_data.get('room', existing_class['room'])
                instructor_to_check = class_data.get('instructor', existing_class['instructor'])

                room_conflicts = self._check_schedule_conflicts(
                    schedules_to_check,
                    room_to_check,
                    exclude_class_id=class_id
                )

                faculty_conflicts = self._check_faculty_schedule_conflicts(
                    schedules_to_check,
                    instructor_to_check,
                    exclude_class_id=class_id
                )

                all_conflicts = room_conflicts + faculty_conflicts

                if all_conflicts:
                    raise ScheduleConflictError(
                        "Schedule conflicts detected:\n" + "\n".join(all_conflicts)
                    )

            if 'section_id' in class_data:
                section = self.section_service.get_by_id(class_data['section_id'])
                class_data['section_name'] = generate_section_name(section) if section else 'Unknown'

            existing_class.update(class_data)
            existing_class['updated_at'] = datetime.now().isoformat()
            existing_class['id'] = class_id

            if 'created_at' not in existing_class:
                existing_class['created_at'] = datetime.now().isoformat()

            self._save_data(data)

            logger.info(f"Updated class ID {class_id}")
            return deepcopy(existing_class)

        except (ClassNotFoundError, ClassValidationError,
                ScheduleConflictError, ClassStorageError):
            raise
        except Exception as e:
            error_msg = f"Unexpected error updating class: {str(e)}"
            logger.error(error_msg)
            raise ClassStorageError(error_msg)

    def delete(self, class_id: int, token: str = None) -> bool:
        """Delete a class. API unchanged."""
        try:
            data = self._load_data()

            original_count = len(data['classes'])
            data['classes'] = [
                cls for cls in data['classes'] if cls.get('id') != class_id
            ]

            if len(data['classes']) == original_count:
                logger.warning(f"Class with ID {class_id} not found")
                return False

            self._save_data(data)
            logger.info(f"Deleted class ID {class_id}")
            return True

        except Exception as e:
            error_msg = f"Error deleting class {class_id}: {str(e)}"
            logger.error(error_msg)
            raise ClassStorageError(error_msg)

    def search(self, filters: Dict, token: str = None) -> List[Dict]:
        """Search classes by criteria. API unchanged."""
        try:
            all_classes = self.get_all(token)

            if not filters:
                return all_classes

            results = []
            for cls in all_classes:
                match = True
                for key, value in filters.items():
                    if key not in cls or cls[key] != value:
                        match = False
                        break
                if match:
                    results.append(cls)

            logger.info(f"Search found {len(results)} classes")
            return results
        except Exception as e:
            logger.error(f"Error searching classes: {str(e)}")
            raise