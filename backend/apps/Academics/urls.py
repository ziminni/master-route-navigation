from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScheduleBlockViewSet, ScheduleEntryViewSet, SemesterViewSet, CurriculumViewSet, \
    ActiveSemesterRetrieveAPIView, SectionViewSet, \
    CourseViewSet, CurriculumCourseListAPIView

from .views import (
    GradingRubricListCreateAPIView,
    GradingRubricDetailAPIView,
    RubricComponentListCreateAPIView,
    RubricComponentDetailAPIView,
    TopicListCreateAPIView,
    TopicDetailAPIView,
    MaterialListCreateAPIView,
    MaterialDetailAPIView,
    AssessmentListCreateAPIView,
    AssessmentDetailAPIView,
    ScoreListCreateAPIView,
    ScoreDetailAPIView,
    BulkScoreCreateAPIView,
    BulkScoreUploadAPIView,
    StudentGradesSummaryAPIView,
    ClassStudentsListAPIView,
)


router = DefaultRouter()
router.register(r'schedule-blocks', ScheduleBlockViewSet, basename='scheduleblock')
router.register(r'schedule-entries', ScheduleEntryViewSet, basename='scheduleentry')


# Funny notes about endpoints for frontend in mod 3 and perhaps other modules, so that we won't forget later on what endpoints are available here:
# GET /api/schedule-blocks/ - List all accessible schedule blocks
# POST /api/schedule-blocks/ - Create a new schedule block
# GET /api/schedule-blocks/{id}/ - Get specific schedule block
# PUT /api/schedule-blocks/{id}/ - Update entire schedule block, As to how to update it exactly. 
#                                   Some wizardry from the frontend is required to comfortably update it efficiently
# PATCH /api/schedule-blocks/{id}/ - Partial update schedule block
# DELETE /api/schedule-blocks/{id}/ - Delete schedule block


# GET /api/schedule-entries/ - List all accessible schedule entries
# POST /api/schedule-entries/ - Create a new schedule entry
# GET /api/schedule-entries/{id}/ - Get specific schedule entry
# PUT /api/schedule-entries/{id}/ - Update entire schedule entry
# PATCH /api/schedule-entries/{id}/ - Partial update schedule entry
# DELETE /api/schedule-entries/{id}/ - Delete schedule entry

router.register(r'semesters', SemesterViewSet, basename='semester')
router.register(r'curriculums', CurriculumViewSet, basename='curriculum')
router.register(r'sections', SectionViewSet, basename='section')
router.register(r'courses', CourseViewSet, basename='course')


urlpatterns = [
    path('active-semester/', ActiveSemesterRetrieveAPIView.as_view(), name='active-semester-retrieve-api-view'),
    path('curriculums/courses/', CurriculumCourseListAPIView.as_view(), name='curriculum-course-list-api-view'),
    # path('sections/', SectionListCreateAPIView.as_view(), name='section-list-api-view'),
    # path('sections/<int:pk>/', SectionRetrieveUpdateDestroyAPIView.as_view(), name='section-retrieve-update-delete-api-view'),

    path(
        'classes/<int:class_id>/grading-rubrics/',
        GradingRubricListCreateAPIView.as_view(),
        name='grading-rubric-list-create'
    ),
    path(
        'grading-rubrics/<int:pk>/',
        GradingRubricDetailAPIView.as_view(),
        name='grading-rubric-detail'
    ),
    path(
        'grading-rubrics/<int:rubric_id>/components/',
        RubricComponentListCreateAPIView.as_view(),
        name='rubric-component-list-create'
    ),
    path(
        'rubric-components/<int:pk>/',
        RubricComponentDetailAPIView.as_view(),
        name='rubric-component-detail'
    ),
    
    path(
        'classes/<int:class_id>/topics/',
        TopicListCreateAPIView.as_view(),
        name='topic-list-create'
    ),
    path(
        'topics/<int:pk>/',
        TopicDetailAPIView.as_view(),
        name='topic-detail'
    ),
    
    path(
        'classes/<int:class_id>/materials/',
        MaterialListCreateAPIView.as_view(),
        name='material-list-create'
    ),
    path(
        'materials/<int:pk>/',
        MaterialDetailAPIView.as_view(),
        name='material-detail'
    ),
    
    path(
        'classes/<int:class_id>/assessments/',
        AssessmentListCreateAPIView.as_view(),
        name='assessment-list-create'
    ),
    path(
        'assessments/<int:pk>/',
        AssessmentDetailAPIView.as_view(),
        name='assessment-detail'
    ),

    path(
        'classes/<int:class_id>/scores/',
        ScoreListCreateAPIView.as_view(),
        name='score-list-create'
    ),
    path(
        'scores/<int:pk>/',
        ScoreDetailAPIView.as_view(),
        name='score-detail'
    ),
    
    # Bulk Operations
    path(
        'classes/<int:class_id>/scores/bulk-create/',
        BulkScoreCreateAPIView.as_view(),
        name='score-bulk-create'
    ),
    path(
        'classes/<int:class_id>/scores/bulk-upload/',
        BulkScoreUploadAPIView.as_view(),
        name='score-bulk-upload'
    ),
    
    path(
        'classes/<int:class_id>/students/<int:student_id>/grades/',
        StudentGradesSummaryAPIView.as_view(),
        name='student-grades-summary'
    ),
    

    path(
        'classes/<int:class_id>/students/',
        ClassStudentsListAPIView.as_view(),
        name='class-students-list'
    ),
    
    path('', include(router.urls)),
]