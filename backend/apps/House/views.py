from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.text import slugify
from . import models, serializers

def _generate_unique_slug(name):
	base = slugify(name)[:200]
	slug = base
	i = 1
	while models.House.objects.filter(slug=slug).exists():
		slug = f"{base}-{i}"
		i += 1
	return slug


class HouseViewSet(viewsets.ModelViewSet):
	"""ViewSet for House objects.

	Uses multipart/form-data parsers so the endpoint accepts image uploads
	for `banner` and `logo`. Creation requires authentication (IsAuthenticatedOrReadOnly
	enforces that non-safe methods require auth).
	"""
	queryset = models.House.objects.all()
	serializer_class = serializers.HouseSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	parser_classes = [MultiPartParser, FormParser]

	def perform_create(self, serializer):
		# Ensure slug is generated and unique when not provided
		name = serializer.validated_data.get("name")
		slug = serializer.validated_data.get("slug")
		if not slug and name:
			slug = _generate_unique_slug(name)
		serializer.save(slug=slug)


class HouseMembershipViewSet(viewsets.ModelViewSet):
	queryset = models.HouseMembership.objects.select_related('user', 'house').all()
	serializer_class = serializers.HouseMembershipSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class HouseEventViewSet(viewsets.ModelViewSet):
	queryset = models.HouseEvent.objects.select_related('house', 'created_by').all()
	serializer_class = serializers.HouseEventSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class EventParticipantViewSet(viewsets.ModelViewSet):
	queryset = models.EventParticipant.objects.select_related('event', 'user').all()
	serializer_class = serializers.EventParticipantSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class AnnouncementViewSet(viewsets.ModelViewSet):
	queryset = models.Announcement.objects.select_related('house', 'author').all()
	serializer_class = serializers.AnnouncementSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]

