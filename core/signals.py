from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_profile_for_new_user(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'profile'):
        base = ''.join(char for char in instance.username.lower() if char.isalnum() or char == '_')[:20] or 'anon'
        pseudonym = base
        counter = 2
        while Profile.objects.filter(pseudonym=pseudonym).exists():
            pseudonym = f'{base[:18]}_{counter}'
            counter += 1
        Profile.objects.create(user=instance, pseudonym=pseudonym)