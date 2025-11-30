from django.contrib import admin
from . import models


@admin.register(models.House)
class HouseAdmin(admin.ModelAdmin):
	list_display = ("name", "members_count", "points_total", "created_at")
	search_fields = ("name",)


@admin.register(models.HouseMembership)
class HouseMembershipAdmin(admin.ModelAdmin):
	list_display = ("user", "house", "role", "points", "is_active")
	list_filter = ("role", "is_active")
	search_fields = ("user__username", "house__name")


@admin.register(models.HouseEvent)
class HouseEventAdmin(admin.ModelAdmin):
	list_display = ("title", "house", "start_date", "is_competition")
	search_fields = ("title", "house__name")


@admin.register(models.EventParticipant)
class EventParticipantAdmin(admin.ModelAdmin):
	list_display = ("event", "user", "confirmed")
	search_fields = ("event__title", "user__username")


@admin.register(models.Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
	list_display = ("title", "house", "author", "created_at")
	search_fields = ("title", "house__name", "author__username")
