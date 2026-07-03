from django.db.models import Q
from django.utils import timezone

import django_filters

from profiles.models import Language, Profile

from .models import JobPosting


class JobPostingFilter(django_filters.FilterSet):
    category = django_filters.ChoiceFilter(choices=Profile.UserCategory.choices)
    province = django_filters.NumberFilter(field_name='province_id')
    city = django_filters.NumberFilter(field_name='city_id')
    salary_min = django_filters.NumberFilter(method='filter_salary_min')
    experience_required = django_filters.ChoiceFilter(choices=JobPosting.ExperienceRequired.choices)
    sect = django_filters.ChoiceFilter(choices=JobPosting.Sect.choices)
    required_languages = django_filters.ModelMultipleChoiceFilter(
        field_name='required_languages',
        queryset=Language.objects.all(),
    )

    class Meta:
        model = JobPosting
        fields = [
            'category',
            'province',
            'city',
            'salary_min',
            'experience_required',
            'sect',
            'required_languages',
        ]

    def filter_salary_min(self, queryset, name, value):
        if value is None:
            return queryset
        return queryset.filter(
            Q(salary_max__gte=value)
            | Q(salary_max__isnull=True, salary_min__gte=value)
        ).distinct()
