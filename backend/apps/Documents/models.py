from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import os
import mimetypes
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from .mixins import ActivityTrackingMixin

# Constants
BYTES_PER_MB = 1024 * 1024

def document_upload_path(instance, filename):
    name, ext = os.path.splitext(filename)
    safe_name = slugify(name)
    # Ensure category slug is also safe
    safe_category = slugify(instance.category.slug)
    # Limit extension length to prevent abuse
    safe_ext = ext[:10].lower()
    return f'documents/{safe_category}/{safe_name}{safe_ext}'

User = get_user_model()

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        ordering = ['display_order']
        indexes = [
            models.Index(fields=['display_order', 'slug'])
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class DocumentType(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    allowed_extensions = models.JSONField(default=list)  # Native JSON field

    max_file_size_mb = models.IntegerField(
        default=10,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(100)
            ]
    )

    requires_approval = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'document_types'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug'])
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Folder(models.Model):
    """Hierarchical folder structure for organizing documents"""
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='subfolders'
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='folders',
        help_text="Root category for this folder"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_folders'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Permissions
    is_public = models.BooleanField(
        default=True,
        help_text="If False, only users with explicit permissions can access"
    )
    
    # Soft delete
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='deleted_folders'
    )
    
    class Meta:
        db_table = 'folders'
        ordering = ['name']
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['category']),
            models.Index(fields=['created_by']),
            models.Index(fields=['deleted_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['parent', 'name'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_folder_name_per_parent'
            )
        ]
    
    def __str__(self):
        return self.get_full_path()
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_full_path(self):
        """Get the full path like /Academic/CS101/Lectures"""
        if self.parent:
            return f"{self.parent.get_full_path()}/{self.name}"
        return f"/{self.name}"
    
    def get_ancestors(self):
        """Get all parent folders up to root"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors
    
    def get_descendants(self):
        """Get all child folders recursively"""
        descendants = list(self.subfolders.filter(deleted_at__isnull=True))
        for subfolder in list(descendants):
            descendants.extend(subfolder.get_descendants())
        return descendants
    
    def can_user_access(self, user, action='view'):
        """Check if user can perform action on this folder"""
        if not user or not user.is_authenticated:
            return self.is_public and action == 'view'
        
        # Admin can do everything
        if user.role_type == 'admin':
            return True
        
        # Check folder permissions
        permission = self.folder_permissions.filter(user=user).first()
        if permission:
            if action == 'view':
                return permission.can_view
            elif action == 'upload':
                return permission.can_upload
            elif action == 'edit':
                return permission.can_edit
            elif action == 'delete':
                return permission.can_delete
        
        # Check role-based permissions
        role_permission = self.folder_role_permissions.filter(role=user.role_type).first()
        if role_permission:
            if action == 'view':
                return role_permission.can_view
            elif action == 'upload':
                return role_permission.can_upload
            elif action == 'edit':
                return role_permission.can_edit
            elif action == 'delete':
                return role_permission.can_delete
        
        # Faculty can access their own folders
        if user.role_type == 'faculty' and self.created_by == user:
            return True
        
        # Default: students can view public folders
        if self.is_public and action == 'view':
            return True
        
        return False

class FolderPermission(models.Model):
    """User-specific permissions for folders"""
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        related_name='folder_permissions'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='folder_permissions'
    )
    
    can_view = models.BooleanField(default=True)
    can_upload = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'folder_permissions'
        unique_together = [['folder', 'user']]
        indexes = [
            models.Index(fields=['folder']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.folder.name}"

class FolderRolePermission(models.Model):
    """Role-based permissions for folders"""
    
    class Roles(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        STUDENT = 'student', 'Student'
        FACULTY = 'faculty', 'Faculty'
        STAFF = 'staff', 'Staff'
    
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        related_name='folder_role_permissions'
    )
    
    role = models.CharField(
        max_length=50,
        choices=Roles.choices
    )
    
    can_view = models.BooleanField(default=True)
    can_upload = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'folder_role_permissions'
        unique_together = [['folder', 'role']]
        indexes = [
            models.Index(fields=['folder']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.role} - {self.folder.name}"

class ActiveDocumentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True, deleted_at__isnull=True)

class Document(ActivityTrackingMixin, models.Model):
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    file_path = models.FileField(upload_to=document_upload_path)
    file_size = models.PositiveBigIntegerField(null=True, blank=True)
    file_extension = models.CharField(max_length=10, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='documents'
    )
    
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='documents',
        help_text="Folder where this document is stored"
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='uploaded_documents',
    )

    # Commented — no organization model yet
    # organization = models.ForeignKey(
    # Organizations,
    # on_delete=models.SET_NULL,
    # null=True, blank=True
    # )
    
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='documents'
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    view_count = models.IntegerField(default=0)

    is_featured = models.BooleanField(default=False)
    
    # Soft delete fields
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='deleted_documents'
    )

    # Custom managers
    objects = models.Manager()
    active = ActiveDocumentManager()

    class Meta:
        db_table = 'documents'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['category', '-uploaded_at']),
            models.Index(fields=['uploaded_by']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['document_type']),
            models.Index(fields=['title']),
            models.Index(fields=['deleted_at']),
            models.Index(fields=['folder']),
        ]
        
        constraints = [
            models.CheckConstraint(
                check=models.Q(file_size__gte=0),
                name='positive_file_size'
            )
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def file_size_mb(self):
        """Return file size in megabytes"""
        if self.file_size:
            return round(self.file_size / BYTES_PER_MB, 2)
        return 0
    
    @property
    def can_be_downloaded(self):
        """Check if document is active and approved if needed"""
        if not self.is_active:
            return False
        if self.document_type and self.document_type.requires_approval:
            return hasattr(self, 'approval') and self.approval.status == 'approved'
        return True
    
    def get_download_count(self):
        """Get number of downloads from activity log (use in querysets with annotations)"""
        return self.get_activity_count(
            action=ActivityLog.ActionTypes.DOCUMENT_DOWNLOAD
        )
    
    def increment_view_count(self):
        """Atomically increment view count"""
        from django.db.models import F
        Document.objects.filter(pk=self.pk).update(view_count=F('view_count') + 1)
        self.refresh_from_db()
    
    def can_user_access(self, user, action='view'):
        """Check if user can perform action on this document"""
        if not user or not user.is_authenticated:
            # Anonymous users can only view if no approval required
            if action == 'view' and not self.document_type:
                return True
            if action == 'view' and self.document_type and not self.document_type.requires_approval:
                return True
            return False
        
        # Admin can do everything
        if user.role_type == 'admin':
            return True
        
        # Faculty can do everything with their own documents
        if user.role_type == 'faculty' and self.uploaded_by == user:
            return True
        
        # Check folder permissions for actions that modify structure (not view/download)
        # For view and download, we need to check if user can at least view the folder
        if self.folder:
            if action in ['edit', 'delete', 'upload']:
                # For modifying actions, check exact folder permission
                if not self.folder.can_user_access(user, action):
                    return False
            else:
                # For view/download, only require view access to folder
                if not self.folder.can_user_access(user, 'view'):
                    return False
        
        # Check document-specific permissions
        permission = self.permissions.filter(role=user.role_type).first()
        if permission:
            if action == 'view':
                return permission.can_view
            elif action == 'download':
                return permission.can_download and self.can_be_downloaded
            elif action == 'edit':
                return permission.can_edit
            elif action == 'delete':
                return permission.can_delete
        
        # Default role-based permissions
        if user.role_type == 'student':
            # Students can ONLY view and download (if approved), nothing else
            if action in ['view', 'download']:
                return self.can_be_downloaded
            return False
        
        if user.role_type == 'staff':
            # Staff org officers - view and download, upload needs approval
            if action in ['view', 'download']:
                return self.can_be_downloaded
            elif action == 'upload':
                return True  # But requires approval
            return False
        
        return False
    
    def clean(self):
        """Validate document before saving"""
        super().clean()
        
        if self.document_type and self.file_extension:
            allowed = self.document_type.allowed_extensions
            if allowed and self.file_extension.lower() not in allowed:
                raise ValidationError(
                    f"File extension '{self.file_extension}' not allowed. "
                    f"Allowed: {', '.join(allowed)}"
                )
        
        if self.document_type and self.file_size:
            max_size = self.document_type.max_file_size_mb * BYTES_PER_MB
            if self.file_size > max_size:
                raise ValidationError(
                    f"File size exceeds maximum allowed "
                    f"({self.document_type.max_file_size_mb}MB)"
                )
    
    def save(self, *args, **kwargs):
        """Auto-populate file metadata before saving"""
        if self.file_path:
            # Auto-populate file_size
            if not self.file_size and hasattr(self.file_path, 'size'):
                self.file_size = self.file_path.size
            
            # Auto-populate file_extension
            if not self.file_extension:
                _, ext = os.path.splitext(self.file_path.name)
                self.file_extension = ext.lower().lstrip('.')
            
            # Auto-populate mime_type
            if not self.mime_type:
                mime_type, _ = mimetypes.guess_type(self.file_path.name)
                if mime_type:
                    self.mime_type = mime_type
        
        super().save(*args, **kwargs)

class DocumentPermission(models.Model):
    """Role-based permissions for documents (matches BaseUser.ROLE_CHOICES)"""

    class Roles(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        STUDENT = 'student', 'Student'
        FACULTY = 'faculty', 'Faculty'
        STAFF = 'staff', 'Staff'

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='permissions'
        )
    
    role = models.CharField(
        max_length=50,
        choices=Roles.choices,
        default=Roles.STUDENT
        )
    
    can_view = models.BooleanField(default=True)
    can_download = models.BooleanField(default=True)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'document_permissions'
        unique_together = [
            ['document', 'role']
            ]
        indexes = [
            models.Index(fields=['document']),
            models.Index(fields=['role'])
            ]
    
    def __str__(self):
        return f"{self.document.title} - {self.role}"

class DocumentApproval(ActivityTrackingMixin, models.Model):

    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        RESUBMITTED = 'resubmitted', 'Resubmitted'

    document = models.OneToOneField(
        Document,
        on_delete=models.CASCADE,
        related_name='approval'
    )

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )

    previous_status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        blank=True,
        null=True
    )

    resubmission_count = models.IntegerField(default=0)

    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    last_resubmitted_at = models.DateTimeField(blank=True, null=True)

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

    review_notes = models.TextField(blank=True, null=True)
    resubmission_notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'document_approvals'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['reviewed_by'])
        ]
    
    def __str__(self):
        return f"{self.document.title} - {self.status}"
    
    def clean(self):
        """Validate approval status transitions"""
        super().clean()
        
        if self.pk:  # Only validate on updates
            old_instance = DocumentApproval.objects.get(pk=self.pk)
            old_status = old_instance.status
            new_status = self.status
            
            # Define allowed transitions
            ALLOWED_TRANSITIONS = {
                self.StatusChoices.PENDING: [self.StatusChoices.APPROVED, self.StatusChoices.REJECTED],
                self.StatusChoices.REJECTED: [self.StatusChoices.RESUBMITTED],
                self.StatusChoices.RESUBMITTED: [self.StatusChoices.APPROVED, self.StatusChoices.REJECTED],
                self.StatusChoices.APPROVED: [],  # No transitions from approved
            }
            
            if old_status != new_status:
                allowed = ALLOWED_TRANSITIONS.get(old_status, [])
                if new_status not in allowed:
                    raise ValidationError(
                        f"Cannot transition from {old_status} to {new_status}"
                    )
    
    def save(self, *args, **kwargs):
        """Track status changes and update timestamps"""
        from django.utils import timezone
        
        if self.pk:
            old_instance = DocumentApproval.objects.get(pk=self.pk)
            if old_instance.status != self.status:
                self.previous_status = old_instance.status
                
                # Update resubmission tracking
                if self.status == self.StatusChoices.RESUBMITTED:
                    self.resubmission_count += 1
                    self.last_resubmitted_at = timezone.now()
                elif self.status in [self.StatusChoices.APPROVED, self.StatusChoices.REJECTED]:
                    self.reviewed_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Create approval history entry
        if self.pk and self.previous_status:
            ApprovalHistory.objects.create(
                approval=self,
                status_from=self.previous_status,
                status_to=self.status,
                changed_by=self.reviewed_by,
                notes=self.review_notes
            )

class ApprovalHistory(models.Model):

    approval = models.ForeignKey(
        DocumentApproval,
        on_delete=models.CASCADE,
        related_name='history'
    )

    status_from = models.CharField(max_length=20, blank=True, null=True)
    status_to = models.CharField(max_length=20)

    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'approval_history'
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.status_from} → {self.status_to} at {self.changed_at}"

class ActivityLog(models.Model):

    class ActionTypes(models.TextChoices):
        # Document actions
        DOCUMENT_UPLOAD = 'doc_upload', 'Document Uploaded'
        DOCUMENT_UPDATE = 'doc_update', 'Document Updated'
        DOCUMENT_DELETE = 'doc_delete', 'Document Deleted'
        DOCUMENT_VIEW = 'doc_view', 'Document Viewed'
        DOCUMENT_DOWNLOAD = 'doc_download', 'Document Downloaded'
        
        # Approval actions
        APPROVAL_SUBMIT = 'app_submit', 'Approval Submitted'
        APPROVAL_APPROVE = 'app_approve', 'Approval Approved'
        APPROVAL_REJECT = 'app_reject', 'Approval Rejected'
        APPROVAL_RESUBMIT = 'app_resubmit', 'Approval Resubmitted'

        # Version actions
        VERSION_CREATE = 'ver_create', 'Version Created'
        VERSION_ROLLBACK = 'ver_rollback', 'Version Rollback'

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        db_index=True
    )

    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='activities',
        db_index=True
    )

    action = models.CharField(
        max_length=20,
        choices=ActionTypes.choices,
        db_index=True
    )
    
    description = models.TextField(blank=True)

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional data about the action"
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'activity_logs'
        ordering = ['-created_at']
        indexes = [
            # Composite indexes for common queries
            models.Index(fields=['content_type', 'object_id', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            # For analytics queries
            models.Index(fields=['action', 'content_type', '-created_at']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{user_str} {self.get_action_display()} at {self.created_at}"
    
    @classmethod
    def log(cls, action, content_object, user=None, description='', **metadata):
        """
        Helper method to create activity logs easily.
        
        Usage:
            ActivityLog.log(
                action=ActivityLog.ActionTypes.DOCUMENT_DOWNLOAD,
                content_object=document,
                user=request.user,
                description=f"Downloaded {document.title}",
                ip=request.META.get('REMOTE_ADDR')
            )
        """
        return cls.objects.create(
            content_object=content_object,
            user=user,
            action=action,
            description=description,
            metadata=metadata
        )

class DocumentVersion(ActivityTrackingMixin, models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_number = models.IntegerField()
    file_path = models.FileField(upload_to='document_versions/')
    file_size = models.PositiveBigIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)
    change_notes = models.TextField(blank=True, null=True)

    is_current = models.BooleanField(default=False)

    class Meta:
        db_table = 'document_versions'
        unique_together = [['document', 'version_number']]
        ordering = ['-version_number']
        indexes = [
            models.Index(fields=['document']),
            models.Index(fields=['version_number'])
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['document'],
                condition=models.Q(is_current=True),
                name='one_current_version_per_document'
            )
        ]
    
    def __str__(self):
        return f"{self.document.title} v{self.version_number}"