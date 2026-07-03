from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User
from .utils import generate_username, is_valid_pakistani_phone, normalize_phone_number


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
            raise serializers.ValidationError({'non_field_errors': ['invalid credentials']})

        attrs['user'] = user
        return attrs
