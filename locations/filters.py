import django_filters

from .models import City, Province


class ProvinceFilter(django_filters.FilterSet):
    slug = django_filters.CharFilter(field_name='slug', lookup_expr='exact')

    class Meta:
        model = Province
        fields = ['slug']


class CityFilter(django_filters.FilterSet):
    slug = django_filters.CharFilter(field_name='slug', lookup_expr='exact')
    province = django_filters.NumberFilter(field_name='province_id')

    class Meta:
        model = City
        fields = ['slug', 'province']
