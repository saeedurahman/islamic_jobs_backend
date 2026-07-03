from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .filters import CityFilter, ProvinceFilter
from .models import City, District, Province
from .serializers import CitySerializer, DistrictSerializer, ProvinceSerializer


def _apply_filterset(filterset_class, queryset, request):
    filterset = filterset_class(request.query_params, queryset=queryset, request=request)
    if not filterset.is_valid():
        raise ValidationError(filterset.errors)
    return filterset.qs


class ProvinceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProvinceSerializer

    def get_queryset(self):
        return _apply_filterset(ProvinceFilter, Province.objects.all(), self.request)

    @action(detail=True, methods=['get'])
    def cities(self, request, pk=None):
        province = self.get_object()
        serializer = CitySerializer(province.cities.select_related('province').all(), many=True)
        return Response(serializer.data)


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CitySerializer

    def get_queryset(self):
        queryset = _apply_filterset(
            CityFilter,
            City.objects.select_related('province').all(),
            self.request,
        )
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(name_urdu__icontains=search)
                | Q(slug__icontains=search)
            )
        return queryset

    @action(detail=True, methods=['get'])
    def districts(self, request, pk=None):
        city = self.get_object()
        serializer = DistrictSerializer(city.districts.all(), many=True)
        return Response(serializer.data)
