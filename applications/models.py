from django.db import models


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = 'applied', 'Applied'
        SHORTLISTED = 'shortlisted', 'Shortlisted'
        INTERVIEW = 'interview', 'Interview'
        HIRED = 'hired', 'Hired'
        REJECTED = 'rejected', 'Rejected'
        WITHDRAWN = 'withdrawn', 'Withdrawn'

    # Statuses that block a new application to the same job
    ACTIVE_STATUSES = (
        Status.APPLIED,
        Status.SHORTLISTED,
        Status.INTERVIEW,
        Status.HIRED,
    )

    job = models.ForeignKey(
        'jobs.JobPosting',
        on_delete=models.CASCADE,
        related_name='applications',
    )
    applicant = models.ForeignKey(
        'profiles.Profile',
        on_delete=models.CASCADE,
        related_name='applications',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.APPLIED,
    )
    cover_note = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    status_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'applicant'],
                name='unique_job_applicant_application',
            ),
        ]

    def __str__(self):
        return f'{self.applicant} → {self.job.title} ({self.status})'
