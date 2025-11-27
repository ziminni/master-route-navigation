from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import os
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from .mixins import ActivityTrackingMixin

def document_upload_path(instance, filename):
    # Sanitize filename
    name, ext = os.path.splitext(filename)
    safe_name = slugify(name)
    return f'documents/{instance.category.slug}/{safe_name}{ext}'

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

class ActiveDocumentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class Document(ActivityTrackingMixin,models.Model):
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

    tags = models.ManyToManyField(
        'Tag',
        related_name='documents',
        blank=True
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    view_count = models.IntegerField(default=0)

    # Generic relation to activities (reverse relation)
    activities = GenericRelation(
        'ActivityLog',
        related_query_name='document'
    )

    is_featured = models.BooleanField(default=False)

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
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    @property
    def can_be_downloaded(self):
        """Check if document is active and approved if needed"""
        if not self.is_active:
            return False
        if self.document_type and self.document_type.requires_approval:
            return hasattr(self, 'approval') and self.approval.status == 'approved'
        return True
    
    @property
    def download_count(self):
        """Get number of downloads from activity log"""
        return self.get_activity_count(
            action=ActivityLog.ActionTypes.DOCUMENT_DOWNLOAD
        )
    
    @property
    def view_count_from_log(self):
        """Get view count from activity log (alternative to view_count field)"""
        return self.get_activity_count(
            action=ActivityLog.ActionTypes.DOCUMENT_VIEW
        )
    
    def increment_view_count(self):
        """Atomically increment view count"""
        from django.db.models import F
        Document.objects.filter(pk=self.pk).update(view_count=F('view_count') + 1)
        self.refresh_from_db()
    
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
            max_size = self.document_type.max_file_size_mb * 1024 * 1024
            if self.file_size > max_size:
                raise ValidationError(
                    f"File size exceeds maximum allowed "
                    f"({self.document_type.max_file_size_mb}MB)"
                )

class DocumentPermission(models.Model):

    class Roles(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        STUDENT = 'student', 'Student'
        FACULTY = 'faculty', 'Faculty'
        ORG_OFFICER = 'org_officer', 'Organization Officer'

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

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tags'
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

    activities = GenericRelation(
        'ActivityLog',
        related_query_name='approval'
    )

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
    file_size = models.IntegerField(blank=True, null=True)
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)
    change_notes = models.TextField(blank=True, null=True)

    activities = GenericRelation(
        'ActivityLog',
        related_query_name='version'
    )

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