from django.db import models
from django.contrib.auth.models import User 
from django.contrib import admin

class AppointmentScheduleBlock(models.Model):
    faculty = models.ForeignKey(User, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    def __str__(self):
        return self.faculty.username

class AppointmentSchreduleEntry(models.Model):
    schedule_block_entry = models.ForeignKey(AppointmentScheduleBlock, on_delete=models.CASCADE)
    # entry_name = models.CharField(max_length=200)
    start_time = models.TimeField()
    end_time = models.TimeField()
    #0: Sun, 1: Mon, 2: Tue, 3: Wed, 4: Thu, 5: Fri, 6: Sat
    day_of_week = models.SmallIntegerField(default=0)

class Appointment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    appointment_schedule_entry = models.ForeignKey(AppointmentSchreduleEntry, on_delete=models.CASCADE)
    additional_details = models.CharField(max_length=200)
    address = models.CharField(max_length=50)
    #status =  ["pending", "approved", "denied", "rescheduled", "canceled", "completed"]
    status = models.CharField(max_length=15, default="pending")
    appointment_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 
    image_path = models.CharField(max_length=100)


    
