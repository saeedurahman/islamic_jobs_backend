from rest_framework.permissions import BasePermission


class IsJobOwner(BasePermission):
    message = 'You do not have permission to modify this job posting.'

    def has_object_permission(self, request, view, obj):
        try:
            return obj.employer_id == request.user.employer_profile.id
        except Exception:
            return False
