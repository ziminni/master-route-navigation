# backend/apps/Showcase/models.py
from django.conf import settings
from django.db import models


class Media(models.Model):
    MEDIA_TYPES = [
        ("image", "Image"),
        ("video", "Video"),
        ("audio", "Audio"),
        ("file", "File"),
        ("link", "Link"),
    ]

    media_type = models.CharField(max_length=16, choices=MEDIA_TYPES)
    path_or_url = models.TextField()
    mime_type = models.CharField(max_length=255, blank=True, null=True)
    size_bytes = models.BigIntegerField(blank=True, null=True)
    checksum = models.CharField(max_length=255, blank=True, null=True)
    caption = models.CharField(max_length=255, blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="showcase_media",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.caption or f"Media {self.pk}"
    

class ProjectTag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class Project(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("archived", "Archived"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="submitted_projects",
        null=True,
        blank=True,
    )

    # TODO: hook these up to real apps when we see their models
    course_id = models.IntegerField(blank=True, null=True)
    organization_id = models.IntegerField(blank=True, null=True)

    status = models.CharField(max_length=32, blank=True, null=True, choices=STATUS_CHOICES)
    is_public = models.BooleanField(default=False)
    publish_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    category = models.CharField(max_length=100, blank=True, null=True)
    context = models.CharField(max_length=100, blank=True, null=True)
    external_url = models.URLField(blank=True, null=True)
    author_display = models.CharField(max_length=255, blank=True, null=True)

    tags = models.ManyToManyField(ProjectTag, through="ProjectTagMap", related_name="projects")
    media = models.ManyToManyField(Media, through="ProjectMedia", related_name="projects")

    def __str__(self) -> str:
        return self.title


class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="project_memberships")
    role = models.CharField(max_length=100, blank=True, null=True)
    contributions = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("project", "user")

    def __str__(self) -> str:
        return f"{self.user} @ {self.project}"


class ProjectTagMap(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    tag = models.ForeignKey(ProjectTag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("project", "tag")


class ProjectMedia(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    media = models.ForeignKey(Media, on_delete=models.CASCADE)
    sort_order = models.IntegerField(blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "media")


class Competition(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    name = models.CharField(max_length=255)
    organizer = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    related_event_id = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    event_type = models.CharField(max_length=100, blank=True, null=True)
    external_url = models.URLField(blank=True, null=True)

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="submitted_competitions",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=32, default="draft", choices=STATUS_CHOICES)
    is_public = models.BooleanField(default=False)
    publish_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    media = models.ManyToManyField(Media, through="CompetitionMedia", related_name="competitions")

    def __str__(self) -> str:
        return self.name


class CompetitionMedia(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)
    media = models.ForeignKey(Media, on_delete=models.CASCADE)
    sort_order = models.IntegerField(blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("competition", "media")


class CompetitionAchievement(models.Model):
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name="achievements",
        blank=True,
        null=True,
    )
    achievement_title = models.CharField(max_length=255)
    result_recognition = models.CharField(max_length=255, blank=True, null=True)
    specific_awards = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    awarded_at = models.DateField(blank=True, null=True)

    projects = models.ManyToManyField(Project, through="CompetitionAchievementProject", related_name="achievements")
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through="CompetitionAchievementUser", related_name="achievements")

    def __str__(self) -> str:
        return self.achievement_title


class CompetitionAchievementProject(models.Model):
    achievement = models.ForeignKey(CompetitionAchievement, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("achievement", "project")


class CompetitionAchievementUser(models.Model):
    achievement = models.ForeignKey(CompetitionAchievement, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ("achievement", "user")
