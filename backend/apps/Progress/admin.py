from django.contrib import admin
from .models import FinalGrade, GWA, FacultyFeedbackMessage

@admin.register(FinalGrade)
class FinalGradeAdmin(admin.ModelAdmin):
    list_display = ("grade_id", "student", "course", "semester", "final_grade", "status")
    search_fields = ("student__username", "course__code")

@admin.register(GWA)
class GWAAdmin(admin.ModelAdmin):
    list_display = ("gwa_id", "student", "semester", "gwa")
    search_fields = ("student__username",)

@admin.register(FacultyFeedbackMessage)
class FacultyFeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "faculty", "date_sent", "status")
    search_fields = ("student__username", "faculty__username")