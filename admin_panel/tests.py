from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from applications.models import Application
from jobs.models import JobPosting, SavedJob
from notifications.models import Notification
from profiles.models import Profile


class AdminJobRemovalTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            phone_number='03000000001',
            user_role=User.Role.ADMIN,
            password='AdminPassword123!',
        )
        self.seeker_user = User.objects.create_user(
            username='seeker',
            email='seeker@example.com',
            phone_number='03001112222',
            user_role=User.Role.JOB_SEEKER,
            password='OldPassword123!',
        )
        employer_user = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            phone_number='03003334444',
            user_role=User.Role.EMPLOYER,
            password='OldPassword123!',
        )
        self.profile = self.seeker_user.profile
        self.profile.user_category = Profile.UserCategory.IMAM
        self.profile.save(update_fields=['user_category'])
        self.employer = employer_user.employer_profile
        self.employer.organization_name = 'Test Madrasa'
        self.employer.save(update_fields=['organization_name'])
        self.job = self._create_job('Spam Job')
        self.client.force_authenticate(user=self.admin_user)

    def _create_job(self, title):
        return JobPosting.objects.create(
            employer=self.employer,
            title=title,
            description=f'{title} description',
            category=Profile.UserCategory.IMAM,
            experience_required=JobPosting.ExperienceRequired.FRESH,
        )

    def _attach_related_records(self, job):
        application = Application.objects.create(job=job, applicant=self.profile)
        saved_job = SavedJob.objects.create(user=self.seeker_user, job=job)
        job_notification = Notification.objects.create(
            recipient=self.seeker_user,
            notification_type=Notification.NotificationType.JOB_MATCH,
            title='Job match',
            message='A matching job was posted.',
            related_job=job,
        )
        application_notification = Notification.objects.create(
            recipient=self.seeker_user,
            notification_type=Notification.NotificationType.APPLICATION_STATUS_CHANGE,
            title='Application update',
            message='Your application was updated.',
            related_application=application,
        )
        return application, saved_job, job_notification, application_notification

    def test_admin_soft_remove_preserves_related_records_and_admin_list_shows_removed(self):
        application, saved_job, job_notification, application_notification = (
            self._attach_related_records(self.job)
        )

        response = self.client.patch(reverse('admin-job-remove', kwargs={'pk': self.job.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobPosting.Status.REMOVED)
        self.assertTrue(Application.objects.filter(pk=application.pk).exists())
        self.assertTrue(SavedJob.objects.filter(pk=saved_job.pk).exists())
        self.assertTrue(Notification.objects.filter(pk=job_notification.pk).exists())
        self.assertTrue(Notification.objects.filter(pk=application_notification.pk).exists())

        second_response = self.client.patch(reverse('admin-job-remove', kwargs={'pk': self.job.pk}))
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.data['detail'], 'Job is already removed.')

        list_response = self.client.get(reverse('admin-job-list'), {'status': 'removed'})
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data['results'][0]['id'], self.job.pk)
        self.assertEqual(list_response.data['results'][0]['status'], JobPosting.Status.REMOVED)

    def test_admin_hard_delete_cascades_related_records(self):
        application, saved_job, job_notification, application_notification = (
            self._attach_related_records(self.job)
        )

        response = self.client.delete(reverse('admin-job-hard-delete', kwargs={'pk': self.job.pk}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(JobPosting.objects.filter(pk=self.job.pk).exists())
        self.assertFalse(Application.objects.filter(pk=application.pk).exists())
        self.assertFalse(SavedJob.objects.filter(pk=saved_job.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=job_notification.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=application_notification.pk).exists())
