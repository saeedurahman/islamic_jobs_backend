from django.contrib.auth.backends import ModelBackend

from .models import User
from .utils import resolve_user_by_identifier


def is_disabled_job_seeker(user):
    if user.user_role != User.Role.JOB_SEEKER:
        return False
    try:
        return user.profile.is_disabled
    except Exception:
        return False


class EmailOrPhoneBackend(ModelBackend):
    """Authenticate using email or phone number plus password."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if password is None:
            return None

        identifier = kwargs.get('identifier') or username
        if not identifier:
            return None

        user = resolve_user_by_identifier(identifier)
        if user is None:
            return None

        if (
            user.check_password(password)
            and not is_disabled_job_seeker(user)
            and self.user_can_authenticate(user)
        ):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
