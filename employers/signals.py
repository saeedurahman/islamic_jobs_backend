from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User

from .models import Employer


@receiver(post_save, sender=User)
def create_employer_profile(sender, instance, created, **kwargs):
    if created and instance.user_role == User.Role.EMPLOYER:
        Employer.objects.get_or_create(user=instance)
