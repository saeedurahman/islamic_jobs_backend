import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from jobs.models import JobPosting

from .services import create_job_match_notifications

logger = logging.getLogger(__name__)


@receiver(post_save, sender=JobPosting)
def notify_matching_job_seekers_on_job_create(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        count = create_job_match_notifications(instance)
        if count:
            logger.info(
                'Created %s job-match notification(s) for job id=%s',
                count,
                instance.pk,
            )
    except Exception:
        logger.exception(
            'Failed to create job-match notifications for job id=%s',
            instance.pk,
        )
