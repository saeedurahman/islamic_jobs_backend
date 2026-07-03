from django.conf import settings
from django.db import models


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        JOB_MATCH = 'job_match', 'Job Match'
        APPLICATION_STATUS_CHANGE = 'application_status_change', 'Application Status Change'
        OTHER = 'other', 'Other'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_job = models.ForeignKey(
        'jobs.JobPosting',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
    )
    related_application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} → {self.recipient.email}'
