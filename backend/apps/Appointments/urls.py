from django.urls import path

from .views import PlottingScheduleAPIView, BlockEntriesAPIView, RetrieveBlockAPIView, RetrieveAvailableAppointmentsAPIView, RetrieveStudentsAppointmentAPIView, RetrieveFacultyAppointmentAPIView, UpdateAppointmentAPIView, CreateAppointmentAPIView

app_name = "appointment"
urlpatterns = [
    path('plot_schedule/', PlottingScheduleAPIView.as_view(), name='plot_schedule'),
    path('entries/<int:block_id>/', BlockEntriesAPIView.as_view(), name='block_entry'),
    path('retrieve_block/<int:faculty_id>/', RetrieveBlockAPIView.as_view(), name='retrieve_block'),
    path('check_availability/<int:schedule_entry_id>/<str:date>/', RetrieveAvailableAppointmentsAPIView.as_view(), name='retrieve_availability'),
    path('student_appointments/<int:student_id>/', RetrieveStudentsAppointmentAPIView.as_view(), name='student_appointments'),
    path('faculty_appointments/<int:faculty_id>/', RetrieveFacultyAppointmentAPIView.as_view(), name='faculty_appointments'),
    path('update_appointment/<int:id>/', UpdateAppointmentAPIView.as_view(), name='update_appointment'),
    path('create_appointment/', CreateAppointmentAPIView.as_view(), name='create_appointment')
]