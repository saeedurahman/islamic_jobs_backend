from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CityViewSet, ProvinceViewSet

router = DefaultRouter()
router.register('provinces', ProvinceViewSet, basename='province')
router.register('cities', CityViewSet, basename='city')

urlpatterns = [
    path('', include(router.urls)),
]
