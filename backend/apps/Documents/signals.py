from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Document, DocumentApproval, DocumentVersion, ActivityLog

@receiver(post_save, sender=Document)
def log_document_save(sender, instance, created, **kwargs):
    """Automatically log document creation/update"""
    if created:
        instance.log_activity(
            action=ActivityLog.ActionTypes.DOCUMENT_UPLOAD,
            user=instance.uploaded_by,
            description=f"Document '{instance.title}' uploaded"
        )

@receiver(post_delete, sender=Document)
def log_document_delete(sender, instance, **kwargs):
    """Log document deletion and cleanup file"""
    ActivityLog.log(
        action=ActivityLog.ActionTypes.DOCUMENT_DELETE,
        content_object=instance,
        user=None,  # You'll need to pass this from the view
        description=f"Document '{instance.title}' deleted"
    )
    
    # Clean up file
    if instance.file_path:
        instance.file_path.delete(save=False)

@receiver(post_save, sender=DocumentApproval)
def log_approval_status_change(sender, instance, created, **kwargs):
    """Log approval status changes"""
    if not created and instance.previous_status != instance.status:
        action_map = {
            'approved': ActivityLog.ActionTypes.APPROVAL_APPROVE,
            'rejected': ActivityLog.ActionTypes.APPROVAL_REJECT,
            'resubmitted': ActivityLog.ActionTypes.APPROVAL_RESUBMIT,
        }
        
        action = action_map.get(
            instance.status,
            ActivityLog.ActionTypes.APPROVAL_SUBMIT
        )
        
        instance.log_activity(
            action=action,
            user=instance.reviewed_by,
            description=f"Status changed from {instance.previous_status} to {instance.status}",
            review_notes=instance.review_notes
        )

@receiver(post_save, sender=DocumentVersion)
def log_version_creation(sender, instance, created, **kwargs):
    """Log new version creation"""
    if created:
        instance.log_activity(
            action=ActivityLog.ActionTypes.VERSION_CREATE,
            user=instance.uploaded_by,
            description=f"Version {instance.version_number} created",
            change_notes=instance.change_notes
        )

@receiver(post_delete, sender=DocumentVersion)
def delete_version_file(sender, instance, **kwargs):
    """Clean up version file on deletion"""
    if instance.file_path:
        instance.file_path.delete(save=False)