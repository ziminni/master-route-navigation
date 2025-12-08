# backend/apps/Showcase/apps.py
from django.apps import AppConfig


class ShowcaseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.Showcase"   # full Python import path
    # no explicit `label` – let Django default it to "Showcase"
