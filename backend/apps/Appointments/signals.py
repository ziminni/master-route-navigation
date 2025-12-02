from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from datetime import datetime, time, timedelta
from .models import BusyBlock
from apps.Users.models import FacultyProfile
from apps.Calendar.models import Holiday
from apps.Academics.models import Class, ScheduleEntry

User = get_user_model()

def is_valid_schedule_entry(entry):
    """
    Check if a ScheduleEntry has valid data (not blank/empty)
    """
    # Check for required fields
    if not entry.day_of_week or not entry.start_time or not entry.end_time:
        return False
    
    # Check if times are valid
    if entry.end_time <= entry.start_time:
        return False
    
    # Check if schedule block exists
    if not entry.schedule_block_id:
        return False
    
    # Check if semester exists
    if not entry.schedule_block_id.sem_id:
        return False
    
    return True

def generate_busyblocks_from_schedule_entry(entry, faculty, class_instance):
    """Generate BusyBlocks from a ScheduleEntry with validation"""
    
    # Double-check entry is valid
    if not is_valid_schedule_entry(entry):
        return 0
    
    schedule_block = entry.schedule_block_id
    semester = schedule_block.sem_id
    
    if not semester.start_date or not semester.end_date:
        return 0
    
    # Check if semester dates are valid
    if semester.end_date <= semester.start_date:
        return 0
    
    # Day mapping
    day_mapping = {
        'sun': 6, 'mon': 0, 'tue': 1, 'wed': 2, 
        'thu': 3, 'fri': 4, 'sat': 5
    }
    
    target_weekday = day_mapping.get(entry.day_of_week.lower())
    if target_weekday is None:
        return 0
    
    # Determine source model (Class or ScheduleEntry)
    if class_instance:
        source_ct = ContentType.objects.get_for_model(Class)
        source_id = class_instance.id
        note_prefix = f"Class: {class_instance.course.code}"
    else:
        source_ct = ContentType.objects.get_for_model(ScheduleEntry)
        source_id = entry.id
        note_prefix = "Schedule"
    
    # Generate for each week of the semester
    current_date = semester.start_date
    
    # Count created blocks
    blocks_created = 0
    
    while current_date <= semester.end_date:
        if current_date.weekday() == target_weekday:
            # Create datetime
            start_dt = timezone.make_aware(
                datetime.combine(current_date, entry.start_time.time())
            )
            end_dt = timezone.make_aware(
                datetime.combine(current_date, entry.end_time.time())
            )
            
            # Validate time is reasonable
            if (end_dt - start_dt).total_seconds() < 300:  # At least 5 minutes
                current_date += timedelta(days=1)
                continue
            
            BusyBlock.objects.update_or_create(
                faculty=faculty,
                source_ct=source_ct,
                source_id=source_id,
                start_at=start_dt,
                defaults={
                    'end_at': end_dt,
                    'note': f"{note_prefix} - {entry.entry_name}",
                }
            )
            blocks_created += 1
        
        current_date += timedelta(days=1)
    
    return blocks_created

def delete_busyblocks_for_schedule_entry(entry):
    """
    Delete all BusyBlocks associated with a ScheduleEntry
    (When schedule becomes blank/invalid)
    """
    content_type = ContentType.objects.get_for_model(ScheduleEntry)
    BusyBlock.objects.filter(
        source_ct=content_type,
        source_id=entry.id
    ).delete()

def update_busyblocks_for_schedule_entry(entry):
    """
    Update BusyBlocks for a valid ScheduleEntry
    """
    schedule_block = entry.schedule_block_id
    semester = schedule_block.sem_id
    
    # Find all faculty teaching in this semester
    faculty_in_semester = Class.objects.filter(
        semester=semester
    ).exclude(faculty=None).values_list('faculty', flat=True).distinct()
    
    for faculty_id in faculty_in_semester:
        try:
            faculty = FacultyProfile.objects.get(id=faculty_id)
            
            # Delete existing BusyBlocks for this schedule entry
            content_type = ContentType.objects.get_for_model(ScheduleEntry)
            BusyBlock.objects.filter(
                faculty=faculty,
                source_ct=content_type,
                source_id=entry.id
            ).delete()
            
            # Create new BusyBlocks
            generate_busyblocks_from_schedule_entry(entry, faculty, None)
            
        except FacultyProfile.DoesNotExist:
            continue

# ========== SIGNAL HANDLERS ==========

@receiver(post_save, sender=User)
def assign_default_role(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.is_superuser or instance.is_staff:
        return

    if instance.groups.exists():
        return

    if getattr(instance, "role_type", None) == "student":
        student_group, _ = Group.objects.get_or_create(name="student")
        instance.groups.add(student_group)

@receiver(post_save, sender=Holiday)
def create_busy_blocks_for_holiday(sender, instance, created, **kwargs):
    """
    When a Holiday is created/updated, create BusyBlocks for ALL faculty
    Holidays are all-day events that block the entire day
    """
    # Convert holiday date to datetime range (whole day)
    start_at = timezone.make_aware(datetime.combine(instance.date, time.min))
    end_at = timezone.make_aware(datetime.combine(instance.date, time.max))
    
    # Get ContentType for Holiday
    content_type = ContentType.objects.get_for_model(Holiday)
    
    # Get all faculty
    faculty_list = FacultyProfile.objects.all()
    
    for faculty in faculty_list:
        BusyBlock.objects.update_or_create(
            faculty=faculty,
            source_ct=content_type,
            source_id=instance.id,
            defaults={
                'start_at': start_at,
                'end_at': end_at,
                'note': f"Holiday: {instance.name}",
            }
        )

@receiver(post_delete, sender=Holiday)
def delete_busy_blocks_for_holiday(sender, instance, **kwargs):
    """
    Delete all BusyBlocks associated with this holiday when holiday is deleted
    """
    content_type = ContentType.objects.get_for_model(Holiday)
    BusyBlock.objects.filter(
        source_ct=content_type,
        source_id=instance.id
    ).delete()

@receiver(post_save, sender=Class)
def create_busy_blocks_for_class_assignment(sender, instance, created, **kwargs):
    """
    When a Class is assigned to a faculty, create BusyBlocks ONLY if valid schedule exists
    """
    if not instance.faculty:
        return
    
    # Check if this faculty has ANY schedule entries for this semester
    has_schedule = ScheduleEntry.objects.filter(
        schedule_block_id__sem_id=instance.semester
    ).exists()
    
    if not has_schedule:
        # No schedule exists - faculty schedule is blank
        return
    
    # Get ContentType for Class
    content_type = ContentType.objects.get_for_model(Class)
    
    # Find ALL ScheduleEntries for this semester
    schedule_entries = ScheduleEntry.objects.filter(
        schedule_block_id__sem_id=instance.semester
    )
    
    # Create BusyBlocks for each valid schedule entry
    for entry in schedule_entries:
        if is_valid_schedule_entry(entry):
            generate_busyblocks_from_schedule_entry(entry, instance.faculty, instance)

@receiver(post_save, sender=ScheduleEntry)
def handle_schedule_entry_changes(sender, instance, created, **kwargs):
    """
    Handle ScheduleEntry changes - create/update/delete BusyBlocks appropriately
    """
    if is_valid_schedule_entry(instance):
        # Valid schedule - update BusyBlocks
        update_busyblocks_for_schedule_entry(instance)
    else:
        # Invalid/blank schedule - delete associated BusyBlocks
        delete_busyblocks_for_schedule_entry(instance)

@receiver(post_delete, sender=ScheduleEntry)
def delete_busyblocks_on_schedule_delete(sender, instance, **kwargs):
    """Delete BusyBlocks when ScheduleEntry is deleted"""
    delete_busyblocks_for_schedule_entry(instance)