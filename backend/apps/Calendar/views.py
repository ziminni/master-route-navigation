# backend/apps/Calendar/views.py
from rest_framework import viewsets, permissions
from apps.Users import models as user_model
from apps.Announcements import models as announcement_model  # if used

from rest_framework import viewsets, permissions
from .models import CalendarEntry, CalendarLogs, Holiday
from .serializer import (
    CalendarEntrySerializer,
    CalendarLogsSerializer,
    HolidaySerializer,
)


class CalendarEntryViewSet(viewsets.ModelViewSet):
    queryset = CalendarEntry.objects.all().order_by("start_at")
    serializer_class = CalendarEntrySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CalendarLogsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CalendarLogs.objects.select_related("event", "performed_by").all()
    serializer_class = CalendarLogsSerializer
    permission_classes = [permissions.AllowAny]


class HolidayViewSet(viewsets.ModelViewSet):
    queryset = Holiday.objects.all().order_by("date")
    serializer_class = HolidaySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
