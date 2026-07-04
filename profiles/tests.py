from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User

from .models import HifzEducation, Profile


class PublicProfileSearchTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.name_match_user = User.objects.create_user(
            username='imam-profile',
            email='imam-profile@example.com',
            phone_number='03001110000',
            user_role=User.Role.JOB_SEEKER,
            password='OldPassword123!',
        )
        self.education_match_user = User.objects.create_user(
            username='education-profile',
            email='education-profile@example.com',
            phone_number='03002220000',
            user_role=User.Role.JOB_SEEKER,
            password='OldPassword123!',
        )
        self.name_match = self._make_public_profile(
            self.name_match_user.profile,
            full_name='Imam Ahmad',
        )
        self.education_match = self._make_public_profile(
            self.education_match_user.profile,
            full_name='Muhammad Bilal',
        )
        HifzEducation.objects.create(
            profile=self.education_match,
            madrasa_name='Jamia Imam Bukhari',
            completion_year=2015,
        )

    def _make_public_profile(self, profile, full_name):
        profile.full_name = full_name
        profile.user_category = Profile.UserCategory.IMAM
        profile.is_public = True
        profile.verification_status = Profile.VerificationStatus.VERIFIED
        profile.save(
            update_fields=[
                'full_name',
                'user_category',
                'is_public',
                'verification_status',
            ]
        )
        return profile

    def test_profile_search_ranks_name_match_before_education_match(self):
        response = self.client.get(reverse('profile-list'), {'search': 'imam'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [item['id'] for item in response.data['results']]
        self.assertIn(self.name_match.pk, result_ids)
        self.assertIn(self.education_match.pk, result_ids)
        self.assertLess(
            result_ids.index(self.name_match.pk),
            result_ids.index(self.education_match.pk),
        )

    def test_profile_search_allows_typo_with_trigram_similarity(self):
        response = self.client.get(reverse('profile-list'), {'search': 'imaam'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [item['id'] for item in response.data['results']]
        self.assertIn(self.name_match.pk, result_ids)
