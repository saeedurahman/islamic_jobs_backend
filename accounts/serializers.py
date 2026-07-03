import binascii
import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import DjangoUnicodeDecodeError, force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers

from .models import User
from .backends import is_disabled_job_seeker
from .utils import (
    generate_username,
    is_valid_pakistani_phone,
    normalize_phone_number,
    resolve_user_by_identifier,
)

logger = logging.getLogger(__name__)

PASSWORD_RESET_SUCCESS_MESSAGE = (
    'If an account exists with this email/phone, a password reset link has been sent.'
)
PASSWORD_RESET_INVALID_MESSAGE = (
    'This password reset link is invalid or has expired. Please request a new one.'
)
INTERNAL_EMAIL_DOMAINS = ('islamicjobz.internal',)
ACCOUNT_DISABLED_MESSAGE = (
    'This account has been disabled. Contact support if you believe this is an error.'
)


def _format_password_reset_timeout() -> str:
    timeout_seconds = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 60 * 60 * 24 * 3)
    if timeout_seconds % 86400 == 0:
        days = timeout_seconds // 86400
        return f'{days} day' if days == 1 else f'{days} days'
    if timeout_seconds % 3600 == 0:
        hours = timeout_seconds // 3600
        return f'{hours} hour' if hours == 1 else f'{hours} hours'
    return f'{timeout_seconds} seconds'


def _is_deliverable_password_reset_email(email: str) -> bool:
    email = (email or '').strip().lower()
    if not email:
        return False
    return not any(email.endswith(f'@{domain}') for domain in INTERNAL_EMAIL_DOMAINS)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'phone_number',
            'first_name',
            'last_name',
            'user_role',
            'is_phone_verified',
            'created_at',
        ]
        read_only_fields = fields


class MeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = [
            'email',
            'phone_number',
            'password',
            'password_confirm',
            'user_role',
            'first_name',
            'last_name',
        ]

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('email already registered')
        return email

    def validate_phone_number(self, value):
        normalized = normalize_phone_number(value)
        if not is_valid_pakistani_phone(normalized):
            raise serializers.ValidationError(
                'Enter a valid Pakistani phone number (e.g. 03001234567 or +923001234567).'
            )
        if User.objects.filter(phone_number=normalized).exists():
            raise serializers.ValidationError('phone number already registered')
        return normalized

    def validate_user_role(self, value):
        allowed_roles = {User.Role.JOB_SEEKER, User.Role.EMPLOYER}
        if value not in allowed_roles:
            raise serializers.ValidationError(
                'Invalid role. Only job_seeker or employer registration is allowed.'
            )
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'passwords do not match'})
        validate_password(attrs['password'])
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        email = validated_data['email']

        user = User(
            username=generate_username(email),
            **validated_data,
        )
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        from django.contrib.auth import authenticate

        identifier = attrs.get('identifier', '').strip()
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            identifier=identifier,
            password=password,
        )
        if user is None:
            candidate_user = resolve_user_by_identifier(identifier)
            if (
                candidate_user is not None
                and candidate_user.check_password(password)
                and is_disabled_job_seeker(candidate_user)
            ):
                raise serializers.ValidationError(
                    {'non_field_errors': [ACCOUNT_DISABLED_MESSAGE]}
                )
            raise serializers.ValidationError({'non_field_errors': ['invalid credentials']})

        attrs['user'] = user
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField()

    def save(self, **kwargs):
        identifier = self.validated_data['identifier'].strip()
        user = resolve_user_by_identifier(identifier)
        if user is None or not user.is_active or not user.has_usable_password():
            return

        recipient_email = (user.email or '').strip()
        if not _is_deliverable_password_reset_email(recipient_email):
            return

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = (
            f"{settings.FRONTEND_URL}/reset-password?"
            f"{urlencode({'uid': uid, 'token': token})}"
        )
        expiry_label = _format_password_reset_timeout()

        try:
            send_mail(
                subject='Reset your Islamic Jobs password',
                message=(
                    'Assalamu alaikum,\n\n'
                    'We received a request to reset your Islamic Jobs password.\n\n'
                    f'Use this link to choose a new password:\n{reset_url}\n\n'
                    f'This link expires in {expiry_label}. If you did not request this, '
                    'you can safely ignore this email.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
        except Exception:
            logger.exception('Failed to send password reset email for user id=%s', user.pk)


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            User.DoesNotExist,
            DjangoUnicodeDecodeError,
            binascii.Error,
        ):
            raise serializers.ValidationError({'detail': PASSWORD_RESET_INVALID_MESSAGE})

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({'detail': PASSWORD_RESET_INVALID_MESSAGE})

        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'passwords do not match'})

        validate_password(attrs['new_password'], user=user)
        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user
