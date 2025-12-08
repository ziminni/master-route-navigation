"""
Logging service for tracking organization-related actions
"""
from .models import Log


def create_log(user_id: int, action: str, target, organization=None, details: str = ""):
    """
    Create a log entry for an action
    
    Args:
        user_id: The BaseUser ID of the user who performed the action
        action: The action performed (must match Log.Action choices)
        target: The target object (Organization, OrganizationMembers, MembershipApplication, etc.)
        organization: Optional Organization instance for context
        details: Optional additional details about the action
    
    Returns:
        Log instance or None if logging fails
    """
    try:
        # Get target type from the class name
        target_type = target.__class__.__name__
        target_id = target.id if hasattr(target, 'id') else 0
        
        # Create the log entry
        log_entry = Log.objects.create(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id
        )
        
        print(f"LOG: User {user_id} performed '{action}' on {target_type} #{target_id}")
        
        return log_entry
    except Exception as e:
        # Don't let logging errors crash the main operation
        print(f"WARNING: Failed to create log entry - {str(e)}")
        return None


def log_created(user_id: int, target, organization=None, details: str = ""):
    """Log a 'created' action"""
    return create_log(user_id, Log.Action.CREATED, target, organization, details)


def log_edited(user_id: int, target, organization=None, details: str = ""):
    """Log an 'edited' action"""
    return create_log(user_id, Log.Action.EDITED, target, organization, details)


def log_kicked(user_id: int, target, organization=None, details: str = ""):
    """Log a 'kicked' action"""
    return create_log(user_id, Log.Action.KICKED, target, organization, details)


def log_accepted(user_id: int, target, organization=None, details: str = ""):
    """Log an 'accepted' action"""
    return create_log(user_id, Log.Action.ACCEPTED, target, organization, details)


def log_rejected(user_id: int, target, organization=None, details: str = ""):
    """Log a 'rejected' action"""
    return create_log(user_id, Log.Action.REJECTED, target, organization, details)


def log_applied(user_id: int, target, organization=None, details: str = ""):
    """Log an 'applied' action"""
    return create_log(user_id, Log.Action.APPLIED, target, organization, details)


def log_archived(user_id: int, target, organization=None, details: str = ""):
    """Log an 'archived' action"""
    return create_log(user_id, Log.Action.ARCHIVED, target, organization, details)


def log_activated(user_id: int, target, organization=None, details: str = ""):
    """Log an 'activated' action"""
    return create_log(user_id, Log.Action.ACTIVATE, target, organization, details)


def log_deactivated(user_id: int, target, organization=None, details: str = ""):
    """Log a 'deactivated' action"""
    return create_log(user_id, Log.Action.DEACTIVATE, target, organization, details)
