import django_filters
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.db.models import Case, ExpressionWrapper, F, FloatField, Q, Value, When
from django.db.models.functions import Coalesce

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
        search_term = (value or '').strip()
        if not search_term:
            return queryset

        search_vector = (
            SearchVector('full_name', weight='A')
            + SearchVector('hifz_records__madrasa_name', weight='D')
            + SearchVector('dars_nizami_records__madrasa_name', weight='D')
            + SearchVector('mufti_course_records__madrasa_name', weight='D')
            + SearchVector('nazra_qirat_records__madrasa_or_teacher', weight='D')
        )
        search_query = SearchQuery(search_term, search_type='websearch')

        return (
            queryset.annotate(
                search_rank=SearchRank(search_vector, search_query),
                full_name_similarity=Coalesce(
                    TrigramSimilarity('full_name', search_term),
                    Value(0.0),
                ),
                hifz_similarity=Coalesce(
                    TrigramSimilarity('hifz_records__madrasa_name', search_term),
                    Value(0.0),
                ),
                dars_nizami_similarity=Coalesce(
                    TrigramSimilarity(
                        'dars_nizami_records__madrasa_name',
                        search_term,
                    ),
                    Value(0.0),
                ),
                mufti_course_similarity=Coalesce(
                    TrigramSimilarity(
                        'mufti_course_records__madrasa_name',
                        search_term,
                    ),
                    Value(0.0),
                ),
                nazra_qirat_similarity=Coalesce(
                    TrigramSimilarity(
                        'nazra_qirat_records__madrasa_or_teacher',
                        search_term,
                    ),
                    Value(0.0),
                ),
                full_name_match_boost=Case(
                    When(full_name__icontains=search_term, then=Value(5.0)),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
            )
            .annotate(
                search_score=ExpressionWrapper(
                    F('search_rank')
                    + F('full_name_match_boost')
                    + (F('full_name_similarity') * Value(3.0))
                    + (
                        (
                            F('hifz_similarity')
                            + F('dars_nizami_similarity')
                            + F('mufti_course_similarity')
                            + F('nazra_qirat_similarity')
                        )
                        * Value(0.25)
                    ),
                    output_field=FloatField(),
                )
            )
            .filter(
                Q(search_rank__gt=0)
                | Q(full_name_similarity__gt=0.2)
                | Q(hifz_similarity__gt=0.2)
                | Q(dars_nizami_similarity__gt=0.2)
                | Q(mufti_course_similarity__gt=0.2)
                | Q(nazra_qirat_similarity__gt=0.2)
            )
            .order_by('-search_score', '-created_at')
            .distinct()
        )

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
