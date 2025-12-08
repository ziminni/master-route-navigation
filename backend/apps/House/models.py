from django.db import models
from django.conf import settings
from django.utils import timezone


# Common timestamp mixin used across the project style
class TimeStamped(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


def house_banner_upload_to(instance, filename):
	return f"houses/{instance.name.replace(' ', '_')}/banner/{filename}"


class House(TimeStamped):
	name = models.CharField(max_length=200, unique=True)
	slug = models.SlugField(max_length=220, unique=True, blank=True)
	description = models.TextField(blank=True)
	banner = models.ImageField(upload_to=house_banner_upload_to, blank=True, null=True)
	logo = models.ImageField(upload_to=house_banner_upload_to, blank=True, null=True)
	members_count = models.PositiveIntegerField(default=0)
	points_total = models.IntegerField(default=0)
	# New granular point fields
	behavioral_points = models.IntegerField(default=0)
	competitive_points = models.IntegerField(default=0)

	class Meta:
		ordering = ["name"]

	def __str__(self):
		return self.name


class HouseMembership(TimeStamped):
	ROLE_CHOICES = [
		("member", "Member"),
		("leader", "House Leader"),
		("vice_leader", "Vice-House Leader"),
		("secretary", "Secretary"),
		("other", "Other"),
	]

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="house_memberships")
	house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="memberships")
	role = models.CharField(max_length=30, choices=ROLE_CHOICES, default="member")
	year_level = models.CharField(max_length=20, blank=True, null=True)
	avatar = models.CharField(max_length=255, blank=True, null=True)
	points = models.IntegerField(default=0)
	is_active = models.BooleanField(default=True)
	joined_at = models.DateField(default=timezone.now)

	class Meta:
		unique_together = ("user", "house")

	def __str__(self):
		return f"{self.user} @ {self.house} ({self.role})"


class HouseEvent(TimeStamped):
	house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="events")
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	start_date = models.DateTimeField(blank=True, null=True)
	end_date = models.DateTimeField(blank=True, null=True)
	img = models.ImageField(upload_to="houses/events/", blank=True, null=True)
	is_competition = models.BooleanField(default=False)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

	def __str__(self):
		return f"{self.title} ({self.house.name})"


class EventParticipant(TimeStamped):
	event = models.ForeignKey(HouseEvent, on_delete=models.CASCADE, related_name="participants")
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_participations")
	role = models.CharField(max_length=80, blank=True)
	confirmed = models.BooleanField(default=False)

	class Meta:
		unique_together = ("event", "user")

	def __str__(self):
		return f"{self.user} in {self.event.title}"


class Announcement(TimeStamped):
	house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="announcements")
	title = models.CharField(max_length=255)
	content = models.TextField()
	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
	pinned = models.BooleanField(default=False)

	def __str__(self):
		return f"{self.title} - {self.house.name}"
