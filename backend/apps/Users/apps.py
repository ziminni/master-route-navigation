from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.Users'
    label = 'users' 

    def ready(self):
        # import signals
        from . import signals

        # Note: ensure_roles() is intentionally NOT called here to avoid
        # database access during app initialization. Instead, call it manually
        # when needed (e.g., in a management command or during setup script).
        # This prevents the RuntimeWarning about database access in AppConfig.ready()
