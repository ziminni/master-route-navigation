from django.db import models
from backend.apps.Users import models as user_model
from backend.apps.Academics import models as acad_model


# MODULE 6
class EventType:
    # primary id is still automated
    event_type = models.CharField(max_length=50)


# MODULE 6
class EventSchedule(models.Model):
    # Why does this kak exist?
    # The event as a whole is pretty much the EventScheduleBlock
    # This is because the event may go on at an irregular scheduling
    # I just realized this should be connected to the events if that's the case O_O, this is now fixed here.
    # It is now linked to the Event instead of the EventScheduleBlock

    # As usual, the ID is omitted
    event_id = models.ForeignKey('Event', on_delete=models.PROTECT)
    # Perfect example of lazy loading. Because the Event is defined later, we can't just reference it normally. This
    # makes django look up the model later.
    # IMPORTANT:  the syntax for referencing models from different files is
    # 'app_name.ModelName'.the app_name is always the one in the apps.py
    user_id = models.ForeignKey('users.BaseUser')
    # When it's from another app (in this context, users) and we want to implement lazy loading...
    # use the label, not the full app name
    start_time = models.TimeField()
    end_time = models.TimeField()
    creation_date = models.DateTimeField()  # This is when the event was crated


# MODULE 6
class Event(models.Model):
    # Event ID already done over
    org_id = models.ForeignKey(user_model.BaseUser, on_delete=models.PROTECT)
    # Daily reminder that models.PROTECT pretty much prevents deletion of an organization if it has related to it.

    event_type = models.ForeignKey(EventType, on_delete=models.PROTECT)
    event_schedule = models.ForeignKey(EventSchedule, on_delete=models.PROTECT)
    # TODO
    # Commented out since Semester model don't exist yet
    sem_id = models.ForeignKey('Academics.Semester',on_delete=models.PROTECT())

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
    # Assume ID exists because it already does
    event_id = models.ForeignKey(Event, on_delete=models.CASCADE)


# MODULE 6
class EventAttendance(models.Model):
    # ID predeterminado
    event_id = models.ForeignKey(Event, on_delete=models.PROTECT)
    user_id = models.ForeignKey(user_model.BaseUser, on_delete=models.PROTECT)
    time_in = models.DateTimeField()
    time_out = models.DateTimeField()
    notes = models.CharField(max_length=100)


# MODULE 6
class EventApprovals(models.Model):
    # ID included
    event_id = models.ForeignKey('Event', on_delete=models.PROTECT)
    approver_id = models.ForeignKey('users.FacultyProfile', on_delete=models.PROTECT)
    approved_at = models.DateTimeField()
    notes = models.CharField(max_length=100)