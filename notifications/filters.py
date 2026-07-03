import django_filters

from .models import Notification


class NotificationFilter(django_filters.FilterSet):
    is_read = django_filters.BooleanFilter()

    class Meta:
        model = Notification
        fields = ['is_read']
