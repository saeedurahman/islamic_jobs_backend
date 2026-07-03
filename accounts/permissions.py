from rest_framework.permissions import BasePermission

from accounts.backends import is_disabled_job_seeker
from accounts.models import User


class IsAdminUser(BasePermission):
    message = 'Admin access required.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_role == User.Role.ADMIN
        )


class IsJobSeeker(BasePermission):
    message = (
        'Employers do not have job seeker profiles. '
        'Employer profiles are managed separately.'
    )

    def has_permission(self, request, view):
        if not request.user.is_authenticated or request.user.user_role != User.Role.JOB_SEEKER:
            return False
        if is_disabled_job_seeker(request.user):
            self.message = (
                'This account has been disabled. Contact support if you believe this is an error.'
            )
            return False
        return True


class IsEmployer(BasePermission):
    message = (
        'Job seekers do not have employer profiles. '
        'Job seeker profiles are managed separately.'
    )

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_role == User.Role.EMPLOYER
        )
