# compatibility.py (temporary - remove after migration)
class LegacyCompatibilityMixin:
    """Mixin to maintain backward compatibility during migration."""
    
    @property
    def data(self):
        """Legacy data access - warn about deprecated usage."""
        import warnings
        warnings.warn("Direct data access is deprecated. Use service methods instead.", 
                     DeprecationWarning, stacklevel=2)
        return self._data
    
    def filter_classwork(self, class_id, filter_type=None, topic_name=None):
        """Legacy method signature for backward compatibility."""
        return self.filter_classwork(class_id, filter_type, topic_name)