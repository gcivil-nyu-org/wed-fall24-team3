from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event, ChatRoom


@receiver(post_save, sender=Event)
def create_chat_room(sender, instance, created, **kwargs):
    # Check if the event is newly created and has a valid 'created_by' field
    if created and instance.created_by:
        ChatRoom.objects.create(event=instance, creator=instance.created_by)
