# backend/apps/Calendar/urls.py
from rest_framework.routers import DefaultRouter
from .views import CalendarEntryViewSet, CalendarLogsViewSet, HolidayViewSet

router = DefaultRouter()
router.register(r"calendar-entries", CalendarEntryViewSet, basename="calendar-entry")
router.register(r"calendar-logs", CalendarLogsViewSet, basename="calendar-logs")
router.register(r"holidays", HolidayViewSet, basename="holidays")

urlpatterns = router.urls
