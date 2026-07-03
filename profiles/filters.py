import django_filters
from django.db.models import Q

from .models import Profile


class PublicProfileFilter(django_filters.FilterSet):
    user_category = django_filters.ChoiceFilter(choices=Profile.UserCategory.choices)
    province = django_filters.NumberFilter(field_name='province_id')
    city = django_filters.NumberFilter(field_name='city_id')
    has_hifz = django_filters.BooleanFilter(method='filter_has_hifz')
    has_dars_nizami = django_filters.BooleanFilter(method='filter_has_dars_nizami')
    languages = django_filters.NumberFilter(method='filter_languages')
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Profile
        fields = [
            'user_category',
            'province',
            'city',
            'has_hifz',
            'has_dars_nizami',
            'languages',
            'search',
        ]

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(full_name__icontains=value)
            | Q(hifz_records__madrasa_name__icontains=value)
            | Q(dars_nizami_records__madrasa_name__icontains=value)
            | Q(mufti_course_records__madrasa_name__icontains=value)
            | Q(nazra_qirat_records__madrasa_or_teacher__icontains=value)
        ).distinct()

    def filter_has_hifz(self, queryset, name, value):
        if value is True:
            return queryset.filter(hifz_records__isnull=False).distinct()
        return queryset

    def filter_has_dars_nizami(self, queryset, name, value):
        if value is True:
            return queryset.filter(dars_nizami_records__isnull=False).distinct()
        return queryset

    def filter_languages(self, queryset, name, value):
        if value:
            return queryset.filter(languages__id=value).distinct()
        return queryset
