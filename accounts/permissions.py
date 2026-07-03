from rest_framework.permissions import BasePermission

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
        return (
            request.user.is_authenticated
            and request.user.user_role == User.Role.JOB_SEEKER
        )


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
