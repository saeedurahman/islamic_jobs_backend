from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        JOB_SEEKER = 'job_seeker', 'Job Seeker'
        EMPLOYER = 'employer', 'Employer'
        ADMIN = 'admin', 'Admin'

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    user_role = models.CharField(max_length=20, choices=Role.choices)
    is_phone_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email
