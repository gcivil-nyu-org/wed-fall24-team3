# Register your models here.
from django.contrib import admin

from .models import Event, UserProfile, CreatorProfile

admin.site.register(Event)
admin.site.register(UserProfile)
admin.site.register(CreatorProfile)
