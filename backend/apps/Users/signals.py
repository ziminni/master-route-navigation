# backend/apps/Users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

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