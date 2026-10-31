from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, raw=False, **kwargs):
    # Do not create profiles while loading database fixtures.
    if raw:
        return

    if created:
        Profile.objects.get_or_create(user=instance)