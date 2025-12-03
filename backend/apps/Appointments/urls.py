from django.urls import path

from .views import FacultyProfileListView, AvailabilityRuleListView, AvailabilityRuleCreateView, FacultyAvailableScheduleView, AppointmentCreateView, FacultyAppointmentListView, StudentAppointmentListView, AppointmentUpdateView, AllAppointmentListView, StudentProfileListView

app_name = "appointment"
urlpatterns = [
    # path('plot_schedule/', PlottingScheduleAPIView.as_view(), name='plot_schedule'),
    # path('entries/<int:block_id>/', BlockEntriesAPIView.as_view(), name='block_entry'),
    # path('retrieve_block/<int:faculty_id>/', RetrieveBlockAPIView.as_view(), name='retrieve_block'),
    # path('check_availability/<int:schedule_entry_id>/<str:date>/', RetrieveAvailableAppointmentsAPIView.as_view(), name='retrieve_availability'),
    # path('student_appointments/<int:student_id>/', RetrieveStudentsAppointmentAPIView.as_view(), name='student_appointments'),
    # path('faculty_appointments/<int:faculty_id>/', RetrieveFacultyAppointmentAPIView.as_view(), name='faculty_appointments'),
    # path('update_appointment/<int:id>/', UpdateAppointmentAPIView.as_view(), name='update_appointment'),
    # path('create_appointment/', CreateAppointmentAPIView.as_view(), name='create_appointment')
    path('create_availability_rule/', AvailabilityRuleCreateView.as_view(), name='create_availability_rule'),
    path('available_schedule/<int:faculty_id>/<str:date>/', FacultyAvailableScheduleView.as_view(), name='faculty_available_schedule'),
    path('create_appointment/', AppointmentCreateView.as_view(), name='create_appointment'),
    path('faculty_appointment_list/', FacultyAppointmentListView.as_view(), name='faculty_appointments'),
    path('student_appointment_list/', StudentAppointmentListView.as_view(), name='student_appointments'),
    path('update_appointment/<int:id>/', AppointmentUpdateView.as_view(), name='update_appointment'),
    path('get_availability_rule/',  AvailabilityRuleListView.as_view(), name='get_availability_rule'),
    path('faculty_profiles/', FacultyProfileListView.as_view(), name='faculty_profiles_list'),
    path('student_profiles/', StudentProfileListView.as_view(), name='student_profiles_list'),
    path('all_appointment_list/', AllAppointmentListView.as_view(), name='all_appointments'),
    # path('approve_appointment/<int:id>/', FacultyApproveAppointmentView.as_view(), name='faculty_appointment'),
    # path("cancel_appointment/<int:id>/", CancelAppointmentView.as_view(), name="cancel_appointment"),
    # path("reschedule_appointment/<int:id>/", RescheduleAppointmentView.as_view(), name="reschedule_appointment")

]