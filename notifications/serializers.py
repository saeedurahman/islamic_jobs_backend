from rest_framework import serializers

from jobs.models import JobPosting

from .models import Notification


class RelatedJobSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPosting
        fields = ['id', 'title']


class NotificationSerializer(serializers.ModelSerializer):
    related_job = RelatedJobSummarySerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'related_job',
            'is_read',
            'created_at',
        ]
