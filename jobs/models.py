from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from profiles.models import Language, Profile


class JobPosting(models.Model):
    class EmploymentType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full-Time'
        PART_TIME = 'part_time', 'Part-Time'

    class ExperienceRequired(models.TextChoices):
        FRESH = 'fresh', 'Fresh'
        ONE_TO_THREE = '1_3_years', '1–3 years'
        THREE_TO_FIVE = '3_5_years', '3–5 years'
        FIVE_PLUS = '5_plus_years', '5+ years'

    class Sect(models.TextChoices):
        DEOBANDI = 'deobandi', 'Deobandi'
        BARELVI = 'barelvi', 'Barelvi'
        AHLE_HADITH = 'ahle_hadith', 'Ahle Hadith'
        SHIA = 'shia', 'Shia'
        OTHER = 'other', 'Other'
        NOT_SPECIFIED = 'not_specified', 'Not specified'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        CLOSED = 'closed', 'Closed'
        FILLED = 'filled', 'Filled'
        REMOVED = 'removed', 'Removed'

    employer = models.ForeignKey(
        'employers.Employer',
        on_delete=models.CASCADE,
        related_name='job_postings',
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=Profile.UserCategory.choices)
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )

    province = models.ForeignKey(
        'locations.Province',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_postings',
    )
    city = models.ForeignKey(
        'locations.City',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_postings',
    )
    district = models.ForeignKey(
        'locations.District',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_postings',
    )

    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    accommodation_provided = models.BooleanField(default=False)
    meals_provided = models.BooleanField(default=False)
    experience_required = models.CharField(
        max_length=20,
        choices=ExperienceRequired.choices,
    )
    sect = models.CharField(
        max_length=20,
        choices=Sect.choices,
        blank=True,
        null=True,
        help_text='Optional. Sensitive attribute — never required.',
    )
    required_languages = models.ManyToManyField(
        Language,
        blank=True,
        related_name='job_postings',
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            raise ValidationError(
                {'salary_max': 'Maximum salary must be greater than or equal to minimum salary.'}
            )


class SavedJob(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_jobs',
    )
    job = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='saved_by',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} saved {self.job}'
