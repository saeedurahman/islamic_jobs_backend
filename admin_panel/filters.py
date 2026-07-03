import django_filters
from django.db.models import Q

from accounts.models import User
from employers.models import Employer
from jobs.models import JobPosting
from profiles.models import Profile


class AdminProfileFilter(django_filters.FilterSet):
    verification_status = django_filters.ChoiceFilter(choices=Profile.VerificationStatus.choices)
    is_disabled = django_filters.BooleanFilter()
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Profile
        fields = ['verification_status', 'is_disabled']

    def filter_search(self, queryset, name, value):
        if value:
            return queryset.filter(full_name__icontains=value)
        return queryset


class AdminEmployerFilter(django_filters.FilterSet):
    verification_status = django_filters.ChoiceFilter(choices=Employer.VerificationStatus.choices)
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Employer
        fields = ['verification_status']

    def filter_search(self, queryset, name, value):
        if value:
            return queryset.filter(organization_name__icontains=value)
        return queryset


class AdminJobFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=JobPosting.Status.choices)
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = JobPosting
        fields = ['status']

    def filter_search(self, queryset, name, value):
        if value:
            return queryset.filter(title__icontains=value)
        return queryset


class AdminUserFilter(django_filters.FilterSet):
    user_role = django_filters.ChoiceFilter(choices=User.Role.choices)
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = User
        fields = ['user_role']

    def filter_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(email__icontains=value)
                | Q(first_name__icontains=value)
                | Q(last_name__icontains=value)
            )
        return queryset
