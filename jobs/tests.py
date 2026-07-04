from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from profiles.models import Profile

from .models import JobPosting, SavedJob


class SavedJobAPITests(TestCase):
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
        employer_user = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            phone_number='03003334444',
            user_role=User.Role.EMPLOYER,
            password='OldPassword123!',
        )
        self.employer = employer_user.employer_profile
        self.employer.organization_name = 'Test Madrasa'
        self.employer.save(update_fields=['organization_name'])
        self.job = self._create_job('Imam')
        self.other_job = self._create_job('Mufti')

    def _create_job(self, title):
        return JobPosting.objects.create(
            employer=self.employer,
            title=title,
            description=f'{title} job description',
            category=Profile.UserCategory.IMAM,
            experience_required=JobPosting.ExperienceRequired.FRESH,
        )

    def test_save_job_is_idempotent_and_detail_shows_saved_status(self):
        self.client.force_authenticate(user=self.seeker_user)
        save_url = reverse('job-save-toggle', kwargs={'pk': self.job.pk})

        first_response = self.client.post(save_url)
        second_response = self.client.post(save_url)

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(SavedJob.objects.filter(user=self.seeker_user, job=self.job).count(), 1)

        detail_response = self.client.get(reverse('job-detail', kwargs={'pk': self.job.pk}))

        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertIs(detail_response.data['is_saved'], True)

    def test_job_list_marks_saved_jobs_for_authenticated_user(self):
        SavedJob.objects.create(user=self.seeker_user, job=self.job)
        self.client.force_authenticate(user=self.seeker_user)

        response = self.client.get(reverse('job-list-create'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        saved_by_id = {
            item['id']: item['is_saved']
            for item in response.data['results']
        }
        self.assertIs(saved_by_id[self.job.pk], True)
        self.assertIs(saved_by_id[self.other_job.pk], False)

    def test_saved_jobs_list_is_ordered_by_most_recently_saved(self):
        SavedJob.objects.create(user=self.seeker_user, job=self.job)
        SavedJob.objects.create(user=self.seeker_user, job=self.other_job)
        self.client.force_authenticate(user=self.seeker_user)

        response = self.client.get(reverse('job-saved-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item['id'] for item in response.data['results']],
            [self.other_job.pk, self.job.pk],
        )
        self.assertTrue(all(item['is_saved'] for item in response.data['results']))

    def test_unsave_job_deletes_saved_job_or_returns_clear_message(self):
        self.client.force_authenticate(user=self.seeker_user)
        save_url = reverse('job-save-toggle', kwargs={'pk': self.job.pk})
        SavedJob.objects.create(user=self.seeker_user, job=self.job)

        delete_response = self.client.delete(save_url)
        second_delete_response = self.client.delete(save_url)

        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SavedJob.objects.filter(user=self.seeker_user, job=self.job).exists())
        self.assertEqual(second_delete_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_delete_response.data['detail'], 'Job was not saved.')

    def test_anonymous_job_detail_includes_unsaved_status(self):
        response = self.client.get(reverse('job-detail', kwargs={'pk': self.job.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIs(response.data['is_saved'], False)

    def test_removed_job_is_hidden_from_public_detail_but_closed_and_filled_remain_visible(self):
        self.job.status = JobPosting.Status.REMOVED
        self.job.save(update_fields=['status'])
        self.other_job.status = JobPosting.Status.CLOSED
        self.other_job.save(update_fields=['status'])
        filled_job = self._create_job('Filled Job')
        filled_job.status = JobPosting.Status.FILLED
        filled_job.save(update_fields=['status'])

        removed_response = self.client.get(reverse('job-detail', kwargs={'pk': self.job.pk}))
        closed_response = self.client.get(reverse('job-detail', kwargs={'pk': self.other_job.pk}))
        filled_response = self.client.get(reverse('job-detail', kwargs={'pk': filled_job.pk}))

        self.assertEqual(removed_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(closed_response.status_code, status.HTTP_200_OK)
        self.assertEqual(closed_response.data['status'], JobPosting.Status.CLOSED)
        self.assertEqual(filled_response.status_code, status.HTTP_200_OK)
        self.assertEqual(filled_response.data['status'], JobPosting.Status.FILLED)

    def test_job_search_ranks_exact_title_match_before_description_match(self):
        title_match = self._create_job('Senior Imam')
        description_match = self._create_job('Teacher')
        description_match.description = 'Needs an imam for evening classes'
        description_match.save(update_fields=['description'])

        response = self.client.get(reverse('job-list-create'), {'search': 'imam'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [item['id'] for item in response.data['results']]
        self.assertIn(title_match.pk, result_ids)
        self.assertIn(description_match.pk, result_ids)
        self.assertLess(result_ids.index(title_match.pk), result_ids.index(description_match.pk))

    def test_job_search_allows_typo_with_trigram_similarity(self):
        imam_job = self._create_job('Imam')

        response = self.client.get(reverse('job-list-create'), {'search': 'imaam'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [item['id'] for item in response.data['results']]
        self.assertIn(imam_job.pk, result_ids)
