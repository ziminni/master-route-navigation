from django.db import models

class AuthUser(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'auth_user'

    def __str__(self):
        return self.username

class Approvals(models.Model):
    approval_id = models.AutoField(primary_key=True)
    approver = models.ForeignKey(AuthUser, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=30, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'approvals'

class Announcements(models.Model):
    announcement_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    body = models.TextField(null=True, blank=True)

    author = models.ForeignKey(AuthUser, null=True, blank=True, on_delete=models.SET_NULL, related_name="announcement_author")
    publish_at = models.DateTimeField(null=True, blank=True)
    expire_at = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)

    approval = models.ForeignKey(Approvals, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=30, default='draft')
    visibility = models.CharField(max_length=20, default='public')
    priority = models.IntegerField(default=0)
    is_pinned = models.BooleanField(default=False)
    pinned_until = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(AuthUser, null=True, blank=True, on_delete=models.SET_NULL, related_name="announcement_created")
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(AuthUser, null=True, blank=True, on_delete=models.SET_NULL, related_name="announcement_updated")
    deleted_at = models.DateTimeField(null=True, blank=True)

    note = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'announcements'

    def __str__(self):
        return self.title

class Tags(models.Model):
    tag_id = models.AutoField(primary_key=True)
    tag_name = models.CharField(max_length=60, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tags'

    def __str__(self):
        return self.tag_name

class AnnouncementTagMap(models.Model):
    id = models.AutoField(primary_key=True)
    announcement = models.ForeignKey(Announcements, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tags, on_delete=models.CASCADE)

    class Meta:
        db_table = 'announcement_tag_map'

class AnnouncementReads(models.Model):
    read_id = models.AutoField(primary_key=True)
    announcement = models.ForeignKey(Announcements, on_delete=models.CASCADE)
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE)
    has_read = models.BooleanField(default=False)
    read_time = models.DateTimeField(null=True, blank=True)
    device_info = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'announcement_reads'

class AnnouncementAudience(models.Model):
    audience_id = models.AutoField(primary_key=True)
    announcement = models.ForeignKey(Announcements, on_delete=models.CASCADE)
    scope_type = models.CharField(max_length=30)
    scope_target_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'announcement_audience'

class Documents(models.Model):
    document_id = models.AutoField(primary_key=True)
    announcement = models.ForeignKey(Announcements, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=1024)
    mime_type = models.CharField(max_length=100, null=True, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=128, null=True, blank=True)
    uploaded_by = models.ForeignKey(AuthUser, null=True, blank=True, on_delete=models.SET_NULL)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    visible = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    version = models.CharField(max_length=32, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'documents'


class Reminders(models.Model):
    reminder_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    body = models.TextField(null=True, blank=True)
    author = models.ForeignKey(AuthUser, null=True, blank=True, on_delete=models.SET_NULL, related_name="reminder_author")

    remind_at = models.DateTimeField(null=True, blank=True)
    repeat_interval = models.CharField(max_length=50, null=True, blank=True)
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_snoozable = models.BooleanField(default=True)
    snooze_until = models.DateTimeField(null=True, blank=True)
    visibility = models.CharField(max_length=20, default='private')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(AuthUser, null=True, blank=True, on_delete=models.SET_NULL, related_name="reminder_created")
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(AuthUser, null=True, blank=True, on_delete=models.SET_NULL, related_name="reminder_updated")

    expires_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'reminders'

class ReminderAudience(models.Model):
    audience_id = models.AutoField(primary_key=True)
    reminder = models.ForeignKey(Reminders, on_delete=models.CASCADE)
    scope_type = models.CharField(max_length=30)
    scope_target_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'reminder_audience'

class ReminderAcknowledgements(models.Model):
    ack_id = models.AutoField(primary_key=True)
    reminder = models.ForeignKey(Reminders, on_delete=models.CASCADE)
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE)
    acknowledged = models.BooleanField(default=False)
    ack_time = models.DateTimeField(null=True, blank=True)
    device_info = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reminder_acknowledgements'

