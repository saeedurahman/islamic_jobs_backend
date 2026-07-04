from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.serializers import ACCOUNT_DISABLED_MESSAGE
from accounts.models import User
from applications.models import Application
from employers.models import Employer
from jobs.models import JobPosting, SavedJob
from notifications.models import Notification
from profiles.models import HifzEducation, Profile


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


class AdminProfileDisableTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin-profile@example.com',
            phone_number='03000000002',
            user_role=User.Role.ADMIN,
            password='AdminPassword123!',
        )
        self.seeker_user = User.objects.create_user(
            username='seeker-profile',
            email='seeker-profile@example.com',
            phone_number='03005556666',
            user_role=User.Role.JOB_SEEKER,
            password='OldPassword123!',
        )
        employer_user = User.objects.create_user(
            username='employer-profile',
            email='employer-profile@example.com',
            phone_number='03007778888',
            user_role=User.Role.EMPLOYER,
            password='OldPassword123!',
        )
        self.profile = self.seeker_user.profile
        self.profile.full_name = 'Visible Seeker'
        self.profile.user_category = Profile.UserCategory.IMAM
        self.profile.is_public = True
        self.profile.verification_status = Profile.VerificationStatus.VERIFIED
        self.profile.save(
            update_fields=[
                'full_name',
                'user_category',
                'is_public',
                'verification_status',
            ]
        )
        self.employer = employer_user.employer_profile
        self.employer.organization_name = 'Employer Madrasa'
        self.employer.save(update_fields=['organization_name'])
        self.job = JobPosting.objects.create(
            employer=self.employer,
            title='Applicant Review Job',
            description='A job with an applicant',
            category=Profile.UserCategory.IMAM,
            experience_required=JobPosting.ExperienceRequired.FRESH,
        )
        self.application = Application.objects.create(job=self.job, applicant=self.profile)

    def _authenticate_admin(self):
        self.client.force_authenticate(user=self.admin_user)

    def test_admin_disable_hides_public_profile_blocks_login_and_preserves_applicant_view(self):
        self._authenticate_admin()

        response = self.client.patch(
            reverse('admin-profile-disable', kwargs={'pk': self.profile.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.is_disabled)
        self.assertTrue(Application.objects.filter(pk=self.application.pk).exists())

        public_list_response = self.client.get(
            reverse('profile-list'),
            {'search': 'Visible Seeker'},
        )
        public_detail_response = self.client.get(
            reverse('profile-detail', kwargs={'pk': self.profile.pk}),
        )
        self.assertEqual(public_list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(public_list_response.data['count'], 0)
        self.assertEqual(public_detail_response.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(user=None)
        login_response = self.client.post(
            reverse('auth-login'),
            {
                'identifier': 'seeker-profile@example.com',
                'password': 'OldPassword123!',
            },
            format='json',
        )
        self.assertEqual(login_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(login_response.data['non_field_errors'][0]),
            ACCOUNT_DISABLED_MESSAGE,
        )

        self.client.force_authenticate(user=self.employer.user)
        applicant_response = self.client.get(
            reverse('application-job-list', kwargs={'job_id': self.job.pk})
        )
        self.assertEqual(applicant_response.status_code, status.HTTP_200_OK)
        self.assertEqual(applicant_response.data['results'][0]['applicant']['id'], self.profile.pk)

    def test_admin_enable_restores_public_visibility_and_login(self):
        self.profile.is_disabled = True
        self.profile.save(update_fields=['is_disabled'])
        self._authenticate_admin()

        response = self.client.patch(
            reverse('admin-profile-enable', kwargs={'pk': self.profile.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.is_disabled)

        self.client.force_authenticate(user=None)
        public_detail_response = self.client.get(
            reverse('profile-detail', kwargs={'pk': self.profile.pk}),
        )
        login_response = self.client.post(
            reverse('auth-login'),
            {
                'identifier': 'seeker-profile@example.com',
                'password': 'OldPassword123!',
            },
            format='json',
        )
        self.assertEqual(public_detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_admin_profile_list_can_filter_disabled_profiles(self):
        self.profile.is_disabled = True
        self.profile.save(update_fields=['is_disabled'])
        self._authenticate_admin()

        response = self.client.get(reverse('admin-profile-list'), {'is_disabled': 'true'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['id'], self.profile.pk)
        self.assertTrue(response.data['results'][0]['is_disabled'])

    def test_admin_hard_delete_profile_cascades_profile_data_but_keeps_user(self):
        HifzEducation.objects.create(
            profile=self.profile,
            madrasa_name='Test Madrasa',
            completion_year=2010,
        )
        user_id = self.seeker_user.pk
        application_id = self.application.pk
        self._authenticate_admin()

        response = self.client.delete(
            reverse('admin-profile-detail', kwargs={'pk': self.profile.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(User.objects.filter(pk=user_id).exists())
        self.assertFalse(Profile.objects.filter(pk=self.profile.pk).exists())
        self.assertFalse(HifzEducation.objects.filter(profile_id=self.profile.pk).exists())
        self.assertFalse(Application.objects.filter(pk=application_id).exists())


class AdminUserHardDeleteTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin-user-delete',
            email='admin-user-delete@example.com',
            phone_number='03000000003',
            user_role=User.Role.ADMIN,
            password='AdminPassword123!',
        )
        self.client.force_authenticate(user=self.admin_user)

    def _create_employer_user(self, suffix=''):
        employer_user = User.objects.create_user(
            username=f'employer-delete{suffix}',
            email=f'employer-delete{suffix}@example.com',
            phone_number=f'0311111111{suffix or 0}',
            user_role=User.Role.EMPLOYER,
            password='OldPassword123!',
        )
        employer = employer_user.employer_profile
        employer.organization_name = 'Delete Test Employer'
        employer.save(update_fields=['organization_name'])
        return employer_user

    def _create_job(self, employer):
        return JobPosting.objects.create(
            employer=employer,
            title='Delete Test Job',
            description='A job for cascade testing.',
            category=Profile.UserCategory.IMAM,
            employment_type=JobPosting.EmploymentType.FULL_TIME,
            experience_required=JobPosting.ExperienceRequired.FRESH,
        )

    def test_admin_can_hard_delete_job_seeker_and_reuse_email_phone(self):
        seeker_user = User.objects.create_user(
            username='delete-seeker',
            email='delete-seeker@example.com',
            phone_number='03009990000',
            user_role=User.Role.JOB_SEEKER,
            password='OldPassword123!',
        )
        employer_user = self._create_employer_user('1')
        profile = seeker_user.profile
        profile.full_name = 'Delete Seeker'
        profile.user_category = Profile.UserCategory.IMAM
        profile.save(update_fields=['full_name', 'user_category'])
        HifzEducation.objects.create(
            profile=profile,
            madrasa_name='Delete Test Madrasa',
            completion_year=2012,
        )
        job = self._create_job(employer_user.employer_profile)
        application = Application.objects.create(job=job, applicant=profile)
        saved_job = SavedJob.objects.create(user=seeker_user, job=job)
        recipient_notification = Notification.objects.create(
            recipient=seeker_user,
            notification_type=Notification.NotificationType.JOB_MATCH,
            title='Saved job reminder',
            message='A reminder.',
            related_job=job,
        )
        application_notification = Notification.objects.create(
            recipient=employer_user,
            notification_type=Notification.NotificationType.APPLICATION_STATUS_CHANGE,
            title='Application update',
            message='An application update.',
            related_application=application,
        )

        response = self.client.delete(
            reverse('admin-user-hard-delete', kwargs={'pk': seeker_user.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=seeker_user.pk).exists())
        self.assertFalse(Profile.objects.filter(pk=profile.pk).exists())
        self.assertFalse(HifzEducation.objects.filter(profile_id=profile.pk).exists())
        self.assertFalse(Application.objects.filter(pk=application.pk).exists())
        self.assertFalse(SavedJob.objects.filter(pk=saved_job.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=recipient_notification.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=application_notification.pk).exists())

        self.client.force_authenticate(user=None)
        register_response = self.client.post(
            reverse('auth-register'),
            {
                'email': 'delete-seeker@example.com',
                'phone_number': '03009990000',
                'password': 'NewPassword123!',
                'password_confirm': 'NewPassword123!',
                'user_role': User.Role.JOB_SEEKER,
                'first_name': 'New',
                'last_name': 'Seeker',
            },
            format='json',
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_hard_delete_employer_and_cascade_jobs(self):
        employer_user = self._create_employer_user('2')
        seeker_user = User.objects.create_user(
            username='delete-employer-applicant',
            email='delete-employer-applicant@example.com',
            phone_number='03008880000',
            user_role=User.Role.JOB_SEEKER,
            password='OldPassword123!',
        )
        profile = seeker_user.profile
        profile.user_category = Profile.UserCategory.IMAM
        profile.save(update_fields=['user_category'])
        employer = employer_user.employer_profile
        job = self._create_job(employer)
        application = Application.objects.create(job=job, applicant=profile)
        saved_job = SavedJob.objects.create(user=seeker_user, job=job)
        employer_notification = Notification.objects.create(
            recipient=employer_user,
            notification_type=Notification.NotificationType.OTHER,
            title='Employer notification',
            message='A notification.',
        )
        job_notification = Notification.objects.create(
            recipient=seeker_user,
            notification_type=Notification.NotificationType.JOB_MATCH,
            title='Job notification',
            message='A job notification.',
            related_job=job,
        )

        response = self.client.delete(
            reverse('admin-user-hard-delete', kwargs={'pk': employer_user.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=employer_user.pk).exists())
        self.assertFalse(Employer.objects.filter(pk=employer.pk).exists())
        self.assertFalse(JobPosting.objects.filter(pk=job.pk).exists())
        self.assertFalse(Application.objects.filter(pk=application.pk).exists())
        self.assertFalse(SavedJob.objects.filter(pk=saved_job.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=employer_notification.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=job_notification.pk).exists())

    def test_admin_user_hard_delete_blocks_self_delete_and_admin_targets(self):
        other_admin = User.objects.create_user(
            username='other-admin',
            email='other-admin@example.com',
            phone_number='03007770000',
            user_role=User.Role.ADMIN,
            password='AdminPassword123!',
        )

        self_response = self.client.delete(
            reverse('admin-user-hard-delete', kwargs={'pk': self.admin_user.pk})
        )
        other_admin_response = self.client.delete(
            reverse('admin-user-hard-delete', kwargs={'pk': other_admin.pk})
        )

        self.assertEqual(self_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self_response.data['detail'],
            'You cannot delete your own admin account.',
        )
        self.assertEqual(other_admin_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            other_admin_response.data['detail'],
            'Admin accounts cannot be deleted from this endpoint.',
        )
        self.assertTrue(User.objects.filter(pk=self.admin_user.pk).exists())
        self.assertTrue(User.objects.filter(pk=other_admin.pk).exists())
