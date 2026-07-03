from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from jobs.models import JobPosting
from profiles.models import Profile


class ApplicationCreateThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.seeker_user = User.objects.create_user(
            username='seeker',
            email='seeker@example.com',
            phone_number='03001112222',
            user_role=User.Role.JOB_SEEKER,
            password='OldPassword123!',
        )
        profile = self.seeker_user.profile
        profile.full_name = 'Test Seeker'
        profile.user_category = Profile.UserCategory.IMAM
        profile.save(update_fields=['full_name', 'user_category'])
        employer_user = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            phone_number='03003334444',
            user_role=User.Role.EMPLOYER,
            password='OldPassword123!',
        )
        self.employer = employer_user.employer_profile
        self.employer.organization_name = 'Test Madrasa'
        self.employer.contact_email = 'employer@example.com'
        self.employer.save(update_fields=['organization_name', 'contact_email'])
        self.client.force_authenticate(user=self.seeker_user)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_application_create_throttle_blocks_twenty_first_application_per_user(self):
        url = reverse('application-create')
        jobs = [
            JobPosting.objects.create(
                employer=self.employer,
                title=f'Test Job {index}',
                description='Test job description',
                category=Profile.UserCategory.IMAM,
                experience_required=JobPosting.ExperienceRequired.FRESH,
            )
            for index in range(21)
        ]

        responses = [
            self.client.post(url, {'job': job.pk, 'cover_note': 'Interested'}, format='json')
            for job in jobs
        ]

        self.assertEqual(
            [response.status_code for response in responses[:20]],
            [status.HTTP_201_CREATED] * 20,
        )
        self.assertEqual(responses[20].status_code, status.HTTP_429_TOO_MANY_REQUESTS)
