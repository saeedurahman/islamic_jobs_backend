import django_filters

from .models import Application


class ApplicationFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Application.Status.choices)

    class Meta:
        model = Application
        fields = ['status']
