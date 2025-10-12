from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.Users'
    label = 'users' 

    def ready(self):
        # import signals
        from . import signals

        # ensure roles exist
        from .roles import ensure_roles
        try:
            ensure_roles()
        except Exception:
            # Avoid startup crashes during initial migrate (DB might not be ready)
            pass
