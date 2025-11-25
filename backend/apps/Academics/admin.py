from django.contrib import admin
from .models import (
    Semester,
    Curriculum,
    Section,
    Course,
    Class,
    Enrollment,
    GradingRubric,
    RubricComponent,
    Topic,
    Material,
    Assessment,
    Score,
    Attendance,
    ScheduleBlock,
    ScheduleEntry
)

# Basic registrations (no errors)
admin.site.register(Semester)
admin.site.register(Curriculum)
admin.site.register(Section)
admin.site.register(Course)
admin.site.register(Class)
admin.site.register(Enrollment)
admin.site.register(GradingRubric)
admin.site.register(RubricComponent)
admin.site.register(Topic)
admin.site.register(Material)
admin.site.register(Assessment)
admin.site.register(Score)
admin.site.register(Attendance)
admin.site.register(ScheduleBlock)
admin.site.register(ScheduleEntry)