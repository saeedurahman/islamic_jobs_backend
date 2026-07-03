from django.contrib.auth.backends import ModelBackend

from .models import User
from .utils import normalize_phone_number


class EmailOrPhoneBackend(ModelBackend):
    """Authenticate using email or phone number plus password."""

    def authenticate(self, request, identifier=None, password=None, **kwargs):
        if identifier is None or password is None:
            return None

        user = User.objects.filter(email__iexact=identifier).first()
        if user is None:
            normalized_phone = normalize_phone_number(identifier)
            user = User.objects.filter(phone_number=normalized_phone).first()

        if user is None:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
