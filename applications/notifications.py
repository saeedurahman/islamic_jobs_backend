import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _get_employer_email(employer):
    return employer.contact_email or employer.user.email


def _get_applicant_email(profile):
    return profile.contact_email or profile.user.email


def notify_employer_new_application(application):
    try:
        job = application.job
        employer = job.employer
        applicant_name = application.applicant.full_name or application.applicant.user.get_full_name() or 'A job seeker'
        recipient = _get_employer_email(employer)
        send_mail(
            subject=f'New application for {job.title}',
            message=(
                f'You have received a new application for "{job.title}" '
                f'from {applicant_name}.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            'Failed to send new-application email for application id=%s',
            application.pk,
        )


def notify_applicant_status_change(application):
    try:
        job = application.job
        applicant = application.applicant
        recipient = _get_applicant_email(applicant)
        send_mail(
            subject=f'Application status update for {job.title}',
            message=(
                f'Your application for "{job.title}" has been updated. '
                f'New status: {application.get_status_display()}.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            'Failed to send status-update email for application id=%s',
            application.pk,
        )
