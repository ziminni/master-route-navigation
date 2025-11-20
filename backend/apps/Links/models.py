from django.db import models

class ServiceCategory(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        db_table = 'service_categories'

    def __str__(self):
        return self.name


class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name="services")
    service_name = models.CharField(max_length=100)
    service_description = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    email = models.CharField(max_length=100)
    contact = models.CharField(max_length=50)
    logo_path = models.CharField(max_length=100)
    url = models.CharField(max_length=100)

    class Meta:
        db_table = 'services'

    def __str__(self):
        return self.service_name
