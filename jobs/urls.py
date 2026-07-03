from django.urls import path

from .views import (
    JobCategoryCountsView,
    JobDetailView,
    JobListCreateView,
    MyJobsListView,
    SavedJobsListView,
    SavedJobToggleView,
)

urlpatterns = [
    path('my-jobs/', MyJobsListView.as_view(), name='job-my-jobs'),
    path('category-counts/', JobCategoryCountsView.as_view(), name='job-category-counts'),
    path('saved/', SavedJobsListView.as_view(), name='job-saved-list'),
    path('', JobListCreateView.as_view(), name='job-list-create'),
    path('<int:pk>/save/', SavedJobToggleView.as_view(), name='job-save-toggle'),
    path('<int:pk>/', JobDetailView.as_view(), name='job-detail'),
]
