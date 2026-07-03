from django.urls import path

from .views import JobCategoryCountsView, JobDetailView, JobListCreateView, MyJobsListView

urlpatterns = [
    path('my-jobs/', MyJobsListView.as_view(), name='job-my-jobs'),
    path('category-counts/', JobCategoryCountsView.as_view(), name='job-category-counts'),
    path('', JobListCreateView.as_view(), name='job-list-create'),
    path('<int:pk>/', JobDetailView.as_view(), name='job-detail'),
]
