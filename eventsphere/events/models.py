from django.db import models

# Create your models here.
class Event(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    date_time = models.DateTimeField()
    schedule = models.TextField()
    speakers = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name