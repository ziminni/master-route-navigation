from django.db import models
from apps.Users import models as user_model
from apps.Academics import models as acad_model


# MODULE 6
class EventType(models.Model):
    # primary id is still automated
    #Must make sure that it has both behavioral and competitive values
    event_type = models.CharField(max_length=50)
    class Meta:
        db_table = "event_types"



# MODULE 6
class EventSchedule(models.Model):
    # The event as a whole is pretty much the EventScheduleBlock
    # This is because the event may go on at an irregular scheduling
    # I just realized this should be connected to the events if that's the case O_O, this is now fixed here.
    # It is now linked to the Event instead of the EventScheduleBlock
    event_schedule_block_id = models.ForeignKey('EventScheduleBlock', on_delete=models.PROTECT)
    # As usual, the ID is omitted
    event_id = models.ForeignKey('Event', on_delete=models.PROTECT)
    # Perfect example of lazy loading. Because the Event is defined later, we can't just reference it normally. This
    # makes django look up the model later.
    # IMPORTANT:  the syntax for referencing models from different files is
    # 'app_name.ModelName'.the app_name is always the one in the apps.py
    user_id = models.ForeignKey('users.StudentProfile', on_delete=models.PROTECT)
    # When it's from another app (in this context, users) and we want to implement lazy loading...
    # use the label, not the full app name
    start_time = models.TimeField()
    end_time = models.TimeField()
    creation_date = models.DateTimeField()  # This is when the event was crated


# MODULE 6
class Event(models.Model):
    # It had an issue in database diagram where event_schedule_block_id had the event_id instead of the other way around
    # Event ID already done over
    # org_id = models.ForeignKey(user_model.BaseUser, on_delete=models.CASCADE) I need an organization model first
    # You know, consider moving this to Event Schedule Block
    # Daily reminder that models.PROTECT pretty much prevents deletion of an organization if this exists.
    event_schedule_block = models.ForeignKey('EventScheduleBlock', on_delete=models.PROTECT)
    event_type = models.ForeignKey('EventType', on_delete=models.PROTECT)
    # Commented out since Semester model don't exist yet
    sem_id = models.ForeignKey('Academics.Semester',on_delete=models.PROTECT)

    title = models.CharField(max_length=50)
    venue = models.CharField(max_length=100)

    class EventStatus(models.TextChoices):
        # max length is 5 for the codes, should still be recognizable like a mnemonic
        proposed = "prpsd", "proposed"
        approved = "aprvd", "approved"
        completed = "cmplt", "completed"
        rescheduled = "resch", "rescheduled"

    event_status = models.CharField(
        max_length=5,
        choices=EventStatus.choices,
        default=EventStatus.proposed
    )


# MODULE 6
class EventScheduleBlock(models.Model):
    name = models.CharField(max_length=100)  # Name for this schedule block group
    description = models.TextField(blank=True)  # Optional description
    
    class Meta:
        db_table = "event_schedule_blocks"


# MODULE 6
class EventAttendance(models.Model):
    # ID predeterminated
    event_id = models.ForeignKey(Event, on_delete=models.PROTECT)
    student_id = models.ForeignKey(user_model.StudentProfile, on_delete=models.PROTECT)
    # Never use BaseUser for such kak
    time_in = models.DateTimeField()
    time_out = models.DateTimeField()
    notes = models.CharField(max_length=100)
    class Meta:
        db_table = "event_attendance"


# MODULE 6
class EventApproval(models.Model):
    # ID included
    event_id = models.ForeignKey('Event', on_delete=models.PROTECT)
    approver_id = models.ForeignKey(user_model.FacultyProfile, on_delete=models.PROTECT)
    approved_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "event_approvals"
        constraints = [
            models.UniqueConstraint(
                fields=['event_id'],
                name="events_approved_only_once"
                #This ensures event approvals only happen once
            )
        ]