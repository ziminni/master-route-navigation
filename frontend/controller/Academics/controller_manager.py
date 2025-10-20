"""
Singleton manager for shared controller instances.
Ensures all views use the same controller and receive signals.
"""


class ControllerManager:
    """Manages shared controller instances across the application."""

    _instance = None
    _controllers = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_classes_controller(self):
        """
        Get the shared ClassesController instance.
        All views should use this same instance.
        """
        if 'classes_controller' not in self._controllers:
            from frontend.controller.Academics.Tagging.classes_controller import ClassesController
            self._controllers['classes_controller'] = ClassesController()
        return self._controllers['classes_controller']

    def get_sections_controller(self):
        """Get the shared SectionsController instance."""
        if 'sections_controller' not in self._controllers:
            from frontend.controller.Academics.Tagging.sections_controller import SectionsController
            self._controllers['sections_controller'] = SectionsController()
        return self._controllers['sections_controller']