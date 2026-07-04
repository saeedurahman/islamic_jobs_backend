from django.urls import path

from .views import (
    AdminCreateEmployerAndJobView,
    AdminEmployerDetailView,
    AdminEmployerListView,
    AdminEmployerVerifyView,
    AdminJobHardDeleteView,
    AdminJobListView,
    AdminJobRemoveView,
    AdminProfileDisableView,
    AdminProfileDetailView,
    AdminProfileEnableView,
    AdminProfileListView,
    AdminProfileVerifyView,
    AdminStatsView,
    AdminUserHardDeleteView,
    AdminUserListView,
)

urlpatterns = [
    path('create-employer-and-job/', AdminCreateEmployerAndJobView.as_view(), name='admin-create-employer-and-job'),
    path('profiles/', AdminProfileListView.as_view(), name='admin-profile-list'),
    path('profiles/<int:pk>/', AdminProfileDetailView.as_view(), name='admin-profile-detail'),
    path('profiles/<int:pk>/disable/', AdminProfileDisableView.as_view(), name='admin-profile-disable'),
    path('profiles/<int:pk>/enable/', AdminProfileEnableView.as_view(), name='admin-profile-enable'),
    path('profiles/<int:pk>/verify/', AdminProfileVerifyView.as_view(), name='admin-profile-verify'),
    path('employers/', AdminEmployerListView.as_view(), name='admin-employer-list'),
    path('employers/<int:pk>/', AdminEmployerDetailView.as_view(), name='admin-employer-detail'),
    path('employers/<int:pk>/verify/', AdminEmployerVerifyView.as_view(), name='admin-employer-verify'),
    path('jobs/', AdminJobListView.as_view(), name='admin-job-list'),
    path('jobs/<int:pk>/remove/', AdminJobRemoveView.as_view(), name='admin-job-remove'),
    path('jobs/<int:pk>/', AdminJobHardDeleteView.as_view(), name='admin-job-hard-delete'),
    path('users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('users/<int:pk>/', AdminUserHardDeleteView.as_view(), name='admin-user-hard-delete'),
    path('stats/', AdminStatsView.as_view(), name='admin-stats'),
]
