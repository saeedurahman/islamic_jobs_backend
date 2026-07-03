from django.urls import path

from .views import MeProfileView, ProfileDetailView, ProfileListView
from .views_education import (
    AsriEducationCreateView,
    AsriEducationDetailView,
    DarseNizamiCreateView,
    DarseNizamiDetailView,
    HifzEducationCreateView,
    HifzEducationDetailView,
    IjazahCreateView,
    IjazahDetailView,
    MuftiCourseCreateView,
    MuftiCourseDetailView,
    NazraQiratCreateView,
    NazraQiratDetailView,
)

urlpatterns = [
    path('me/hifz/', HifzEducationCreateView.as_view(), name='profile-hifz-create'),
    path('me/hifz/<int:pk>/', HifzEducationDetailView.as_view(), name='profile-hifz-detail'),
    path('me/dars-nizami/', DarseNizamiCreateView.as_view(), name='profile-dars-nizami-create'),
    path(
        'me/dars-nizami/<int:pk>/',
        DarseNizamiDetailView.as_view(),
        name='profile-dars-nizami-detail',
    ),
    path('me/mufti-course/', MuftiCourseCreateView.as_view(), name='profile-mufti-course-create'),
    path(
        'me/mufti-course/<int:pk>/',
        MuftiCourseDetailView.as_view(),
        name='profile-mufti-course-detail',
    ),
    path('me/ijazah/', IjazahCreateView.as_view(), name='profile-ijazah-create'),
    path('me/ijazah/<int:pk>/', IjazahDetailView.as_view(), name='profile-ijazah-detail'),
    path('me/nazra-qirat/', NazraQiratCreateView.as_view(), name='profile-nazra-qirat-create'),
    path(
        'me/nazra-qirat/<int:pk>/',
        NazraQiratDetailView.as_view(),
        name='profile-nazra-qirat-detail',
    ),
    path(
        'me/asri-education/',
        AsriEducationCreateView.as_view(),
        name='profile-asri-education-create',
    ),
    path(
        'me/asri-education/<int:pk>/',
        AsriEducationDetailView.as_view(),
        name='profile-asri-education-detail',
    ),
    path('me/', MeProfileView.as_view(), name='profile-me'),
    path('', ProfileListView.as_view(), name='profile-list'),
    path('<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),
]
