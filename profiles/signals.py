from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from accounts.models import User

from .models import (
    AsriEducation,
    DarseNizami,
    HifzEducation,
    Ijazah,
    MuftiCourse,
    NazraQirat,
    Profile,
)


def update_profile_completion_percentage(profile):
    """Recalculate and persist profile completion without infinite signal loops."""
    new_percentage = profile.calculate_completion_percentage()
    if profile.profile_completion_percentage != new_percentage:
        profile.profile_completion_percentage = new_percentage
        profile.save(update_fields=['profile_completion_percentage'])


@receiver(post_save, sender=User)
def create_job_seeker_profile(sender, instance, created, **kwargs):
    if created and instance.user_role == User.Role.JOB_SEEKER:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=Profile)
def recalculate_completion_on_profile_save(sender, instance, **kwargs):
    update_fields = kwargs.get('update_fields')
    if update_fields is not None and set(update_fields) <= {'profile_completion_percentage'}:
        return
    update_profile_completion_percentage(instance)


def recalculate_completion_on_education_change(sender, instance, **kwargs):
    update_profile_completion_percentage(instance.profile)


EDUCATION_MODELS = (
    HifzEducation,
    DarseNizami,
    MuftiCourse,
    Ijazah,
    NazraQirat,
    AsriEducation,
)

for _education_model in EDUCATION_MODELS:
    post_save.connect(recalculate_completion_on_education_change, sender=_education_model)
    post_delete.connect(recalculate_completion_on_education_change, sender=_education_model)


@receiver(m2m_changed, sender=Profile.languages.through)
def recalculate_completion_on_languages_changed(sender, instance, action, **kwargs):
    if action in ('post_add', 'post_remove', 'post_clear'):
        update_profile_completion_percentage(instance)


@receiver(m2m_changed, sender=Profile.skills.through)
def recalculate_completion_on_skills_changed(sender, instance, action, **kwargs):
    if action in ('post_add', 'post_remove', 'post_clear'):
        update_profile_completion_percentage(instance)
