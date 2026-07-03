import logging

logger = logging.getLogger(__name__)


def find_matching_profiles(job):
    """Return publicly visible profiles matching a new job posting."""
    from profiles.models import Profile

    if not job.category:
        return Profile.objects.none()

    qs = (
        Profile.objects.filter(
            verification_status=Profile.VerificationStatus.VERIFIED,
            is_public=True,
            user_category=job.category,
        )
        .select_related('user')
        .exclude(user_id=job.employer.user_id)
    )

    if job.city_id:
        qs = qs.filter(city_id=job.city_id)
    elif job.province_id:
        qs = qs.filter(province_id=job.province_id)

    return qs


def _job_location_label(job):
    if job.city_id:
        return job.city.name
    if job.province_id:
        return job.province.name
    return 'Pakistan'


def create_job_match_notifications(job):
    """Create in-app notifications for profiles matching a newly posted job."""
    from jobs.models import JobPosting
    from notifications.models import Notification

    job = (
        JobPosting.objects.select_related('employer', 'city', 'province')
        .get(pk=job.pk)
    )

    matching_profiles = list(find_matching_profiles(job))
    if not matching_profiles:
        return 0

    category_label = job.get_category_display()
    location_label = _job_location_label(job)
    title = f'New {category_label} position in {location_label}'
    message = f"{job.employer.organization_name} is hiring for '{job.title}'"

    notifications = [
        Notification(
            recipient=profile.user,
            notification_type=Notification.NotificationType.JOB_MATCH,
            title=title,
            message=message,
            related_job=job,
        )
        for profile in matching_profiles
    ]
    Notification.objects.bulk_create(notifications)
    return len(notifications)
