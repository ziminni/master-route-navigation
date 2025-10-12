import datetime
from django.forms import ValidationError
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .models import AppointmentScheduleBlock, AppointmentSchreduleEntry, Appointment
from .serializers import AppointmentScheduleBlockSerializer, AppointmentSchreduleEntrySerializer, AppointmentSerializer

"Add new block and entry data"
"request.post"
class PlottingScheduleAPIView(generics.CreateAPIView):
    serializer_class = AppointmentScheduleBlockSerializer

    def create(self, request, *args, **kwargs):
        faculty_id = request.data.get("faculty_id")
        time_slots = request.data.get("time_slots")

        try:
            faculty = User.objects.get(id=faculty_id)
        except User.DoesNotExist:
            return Response({"error": "Faculty not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Step 1: Change is_available of previous blocks
        AppointmentScheduleBlock.objects.filter(faculty=faculty, is_available=True).update(is_available=False)

        # Step 2: Create the block
        block = AppointmentScheduleBlock.objects.create(faculty=faculty)

        # Step 3: Create entries
        entries = []
        for slot in time_slots:
            entry = AppointmentSchreduleEntry.objects.create(
                schedule_block_entry=block,
                start_time=slot["start"],
                end_time=slot["end"],
                day_of_week=slot["day"],
            )
            entries.append(AppointmentSchreduleEntrySerializer(entry).data)

        return Response({
            "message": "Schedule created successfully",
            "block": AppointmentScheduleBlockSerializer(block).data,
            "entries": entries
        }, status=status.HTTP_201_CREATED)
    
"Retrieve a block of a specific faculty and availability"
"request.get"
class RetrieveBlockAPIView(generics.RetrieveAPIView):
    serializer_class = AppointmentScheduleBlockSerializer

    def get_object(self):
        faculty_id = self.kwargs.get("faculty_id")

        try:
            block = AppointmentScheduleBlock.objects.get(
                faculty_id=faculty_id,
                is_available=True
            )
        except AppointmentScheduleBlock.DoesNotExist:
            raise ValidationError("No available schedule block found for this faculty.")

        return block

"List all entries in a specific block_id"
"request.get"
class BlockEntriesAPIView(generics.ListAPIView):
    serializer_class = AppointmentSchreduleEntrySerializer

    def get_queryset(self):
        block_id = self.kwargs.get("block_id")
        return AppointmentSchreduleEntry.objects.filter(schedule_block_entry_id=block_id) if block_id else AppointmentSchreduleEntry.objects.none()
    
"List all Appoinment that mathces the given schedule_entry_id and date" 
"request.get"   
class RetrieveAvailableAppointmentsAPIView(generics.ListAPIView):
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        schedule_entry_id = self.kwargs.get("schedule_entry_id")
        date_str = self.kwargs.get("date")

        if not schedule_entry_id or not date_str:
            raise ValidationError("Both 'schedule_entry_id' and 'date' parameters are required.")

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD.")

        queryset = Appointment.objects.filter(
            appointment_schedule_entry_id=schedule_entry_id,
            appointment_date=date_obj
        )

        return queryset
    
"List all appointment of a specific student"  
"request.get"  
class RetrieveStudentsAppointmentAPIView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    
    def get_queryset(self):
        student_id = self.kwargs.get("student_id")
        return Appointment.objects.filter(student_id=student_id)
    
"List all appointment of a specific faculty"
"request.get"
# get
# post
# put/patch
# delete
class RetrieveFacultyAppointmentAPIView(generics.ListAPIView):
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        faculty_id = self.kwargs.get("faculty_id")
        return Appointment.objects.filter(appointment_schedule_entry__schedule_block_entry__faculty_id=faculty_id)

"""Update an appointment
    the update depends on what the front-end http send to this APIView
    Examples:
        Cancel:  requests.put(f"{API_BASE_URL}{id}/", json={"status": canceled})
        Reschedule:  requests.put(f"{API_BASE_URL}{id}/", json={"status": "reschedules", "appointment_date": "2025-10-6"})
    """
"request.put/patch"    
class UpdateAppointmentAPIView(generics.UpdateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    lookup_field = "id"

"Creates the request"
"request.post"
class CreateAppointmentAPIView(generics.CreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
