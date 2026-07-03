from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import NotificationFilter
from .models import Notification
from .permissions import IsNotificationRecipient
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    filterset_class = NotificationFilter
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        return (
            Notification.objects.filter(recipient=self.request.user)
            .select_related('related_job')
            .order_by('-created_at')
        )


class UnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()
        return Response({'count': count})


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated, IsNotificationRecipient]

    def patch(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk)
        if notification.recipient_id != request.user.id:
            raise PermissionDenied('You do not have permission to access this notification.')
        self.check_object_permissions(request, notification)
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=['is_read'])
        notification = Notification.objects.select_related('related_job').get(pk=notification.pk)
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)
        return Response({'updated': updated}, status=status.HTTP_200_OK)
