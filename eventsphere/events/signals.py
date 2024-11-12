# events/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event, ChatRoom


@receiver(post_save, sender=Event)
def create_chat_room(sender, instance, created, **kwargs):
    if created:
        ChatRoom.objects.create(event=instance, creator=instance.created_by)
