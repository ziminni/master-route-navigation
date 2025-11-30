from django.apps import AppConfig


class HouseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.House'
    label = 'house'

    def ready(self):
        # avoid importing models or running DB queries during migrations/startup
        return
