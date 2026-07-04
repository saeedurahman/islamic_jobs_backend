from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.db.models import ExpressionWrapper, F, FloatField, Q, Value
from django.utils import timezone

import django_filters

from profiles.models import Language, Profile

from .models import JobPosting


class JobPostingFilter(django_filters.FilterSet):
    category = django_filters.ChoiceFilter(choices=Profile.UserCategory.choices)
    employment_type = django_filters.ChoiceFilter(choices=JobPosting.EmploymentType.choices)
    province = django_filters.NumberFilter(field_name='province_id')
    city = django_filters.NumberFilter(field_name='city_id')
    salary_min = django_filters.NumberFilter(method='filter_salary_min')
    experience_required = django_filters.ChoiceFilter(choices=JobPosting.ExperienceRequired.choices)
    sect = django_filters.ChoiceFilter(choices=JobPosting.Sect.choices)
    search = django_filters.CharFilter(method='filter_search')
    required_languages = django_filters.ModelMultipleChoiceFilter(
        field_name='required_languages',
        queryset=Language.objects.all(),
    )

    class Meta:
        model = JobPosting
        fields = [
            'category',
            'employment_type',
            'province',
            'city',
            'salary_min',
            'experience_required',
            'sect',
            'search',
            'required_languages',
        ]

    def filter_salary_min(self, queryset, name, value):
        if value is None:
            return queryset
        return queryset.filter(
            Q(salary_max__gte=value)
            | Q(salary_max__isnull=True, salary_min__gte=value)
        ).distinct()

    def filter_search(self, queryset, name, value):
        search_term = (value or '').strip()
        if not search_term:
            return queryset

        search_vector = (
            SearchVector('title', weight='A')
            + SearchVector('description', weight='B')
        )
        search_query = SearchQuery(search_term, search_type='websearch')

        return (
            queryset.annotate(
                search_rank=SearchRank(search_vector, search_query),
                title_similarity=TrigramSimilarity('title', search_term),
                description_similarity=TrigramSimilarity('description', search_term),
            )
            .annotate(
                search_score=ExpressionWrapper(
                    F('search_rank')
                    + F('title_similarity')
                    + (F('description_similarity') * Value(0.5)),
                    output_field=FloatField(),
                )
            )
            .filter(
                Q(search_rank__gt=0)
                | Q(title_similarity__gt=0.2)
                | Q(description_similarity__gt=0.2)
            )
            .order_by('-search_score', '-created_at')
        )
