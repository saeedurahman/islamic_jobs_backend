from django.urls import path

from .views import (
    ApplicationCreateView,
    ApplicationStatusUpdateView,
    ApplicationWithdrawView,
    JobApplicationsListView,
    MyApplicationsListView,
)

urlpatterns = [
    path('', ApplicationCreateView.as_view(), name='application-create'),
    path('my-applications/', MyApplicationsListView.as_view(), name='application-my-list'),
    path('job/<int:job_id>/', JobApplicationsListView.as_view(), name='application-job-list'),
    path('<int:pk>/status/', ApplicationStatusUpdateView.as_view(), name='application-status'),
    path('<int:pk>/withdraw/', ApplicationWithdrawView.as_view(), name='application-withdraw'),
]
