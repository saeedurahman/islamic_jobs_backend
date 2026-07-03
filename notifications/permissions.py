from rest_framework.permissions import BasePermission


class IsNotificationRecipient(BasePermission):
    message = 'You do not have permission to access this notification.'

    def has_object_permission(self, request, view, obj):
        return obj.recipient_id == request.user.id
