from unittest.mock import Mock, patch

from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient

from .email_backend import ResendAPIBackend
from .models import User
from .serializers import PASSWORD_RESET_INVALID_MESSAGE, PASSWORD_RESET_SUCCESS_MESSAGE


class PasswordResetTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='seeker',
            email='seeker@example.com',
            phone_number='03001112222',
            user_role=User.Role.JOB_SEEKER,
            password='OldPassword123!',
        )

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        FRONTEND_URL='https://www.islamicjobz.com',
    )
    def test_password_reset_request_sends_email_without_leaking_account_existence(self):
        url = reverse('auth-password-reset-request')

        existing_response = self.client.post(
            url,
            {'identifier': '+923001112222'},
            format='json',
        )
        missing_response = self.client.post(
            url,
            {'identifier': 'missing@example.com'},
            format='json',
        )

        self.assertEqual(existing_response.status_code, status.HTTP_200_OK)
        self.assertEqual(missing_response.status_code, status.HTTP_200_OK)
        self.assertEqual(existing_response.data, missing_response.data)
        self.assertEqual(existing_response.data['detail'], PASSWORD_RESET_SUCCESS_MESSAGE)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['seeker@example.com'])
        self.assertIn('Reset your Islamic Jobs password', mail.outbox[0].subject)
        self.assertIn(
            'https://www.islamicjobz.com/reset-password?uid=',
            mail.outbox[0].body,
        )
        self.assertIn('This link expires in 3 days.', mail.outbox[0].body)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_request_skips_internal_placeholder_email(self):
        internal_user = User.objects.create_user(
            username='internal-employer',
            email='internal-employer@islamicjobz.internal',
            phone_number='03003334444',
            user_role=User.Role.EMPLOYER,
            password='OldPassword123!',
        )

        response = self.client.post(
            reverse('auth-password-reset-request'),
            {'identifier': internal_user.phone_number},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], PASSWORD_RESET_SUCCESS_MESSAGE)
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_confirm_updates_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.post(
            reverse('auth-password-reset-confirm'),
            {
                'uid': uid,
                'token': token,
                'new_password': 'NewPassword123!',
                'new_password_confirm': 'NewPassword123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword123!'))

    def test_password_reset_confirm_rejects_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        response = self.client.post(
            reverse('auth-password-reset-confirm'),
            {
                'uid': uid,
                'token': 'invalid-token',
                'new_password': 'NewPassword123!',
                'new_password_confirm': 'NewPassword123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['detail']), PASSWORD_RESET_INVALID_MESSAGE)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPassword123!'))

    def test_existing_login_flow_still_accepts_email_or_phone_identifier(self):
        email_response = self.client.post(
            reverse('auth-login'),
            {'identifier': 'seeker@example.com', 'password': 'OldPassword123!'},
            format='json',
        )
        phone_response = self.client.post(
            reverse('auth-login'),
            {'identifier': '+923001112222', 'password': 'OldPassword123!'},
            format='json',
        )

        self.assertEqual(email_response.status_code, status.HTTP_200_OK)
        self.assertEqual(phone_response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', email_response.data)
        self.assertIn('tokens', phone_response.data)


class AuthThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_login_throttle_blocks_sixth_attempt_from_same_ip(self):
        url = reverse('auth-login')
        payload = {'identifier': 'missing@example.com', 'password': 'WrongPassword123!'}

        responses = [self.client.post(url, payload, format='json') for _ in range(6)]

        self.assertEqual(
            [response.status_code for response in responses[:5]],
            [status.HTTP_400_BAD_REQUEST] * 5,
        )
        self.assertEqual(responses[5].status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Request was throttled.', str(responses[5].data['detail']))

    def test_password_reset_request_throttle_blocks_fourth_attempt_from_same_ip(self):
        url = reverse('auth-password-reset-request')
        payload = {'identifier': 'missing@example.com'}

        responses = [self.client.post(url, payload, format='json') for _ in range(4)]

        self.assertEqual(
            [response.status_code for response in responses[:3]],
            [status.HTTP_200_OK] * 3,
        )
        self.assertEqual(responses[3].status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class ResendAPIBackendTests(TestCase):
    @override_settings(RESEND_API_KEY='re_test_key')
    @patch('accounts.email_backend.requests.post')
    def test_resend_api_backend_sends_django_email_message(self, mock_post):
        response = Mock()
        response.raise_for_status.return_value = None
        mock_post.return_value = response

        backend = ResendAPIBackend()
        email = EmailMessage(
            subject='Test email',
            body='Plain text body',
            from_email='noreply@islamicjobz.com',
            to=['recipient@example.com'],
        )

        sent_count = backend.send_messages([email])

        self.assertEqual(sent_count, 1)
        mock_post.assert_called_once_with(
            'https://api.resend.com/emails',
            json={
                'from': 'noreply@islamicjobz.com',
                'to': ['recipient@example.com'],
                'subject': 'Test email',
                'text': 'Plain text body',
            },
            headers={
                'Authorization': 'Bearer re_test_key',
                'Content-Type': 'application/json',
                'User-Agent': 'IslamicJobsDjango/1.0',
            },
            timeout=10,
        )

    @override_settings(RESEND_API_KEY='re_test_key')
    @patch('accounts.email_backend.requests.post')
    def test_resend_api_backend_honors_fail_silently(self, mock_post):
        mock_post.side_effect = RuntimeError('network failed')
        backend = ResendAPIBackend(fail_silently=True)
        email = EmailMessage(
            subject='Test email',
            body='Plain text body',
            from_email='noreply@islamicjobz.com',
            to=['recipient@example.com'],
        )

        sent_count = backend.send_messages([email])

        self.assertEqual(sent_count, 0)
